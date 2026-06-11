"""Main CLI entry point for password manager."""

import secrets as _secrets

import click
from typing import Optional

from src.password_manager import __version__
from src.password_manager.config import get_settings
from src.password_manager.core import CryptoManager, PasswordGenerator, VaultManager, UserManager
from src.password_manager.storage import DatabaseManager


def _get_authenticated_vault(ctx: click.Context) -> tuple:
    """Prompt for credentials, authenticate, and return (vault_manager, crypto_manager, db_manager)."""
    username = click.prompt("Username")
    master_password = click.prompt("Master Password", hide_input=True)

    db_manager = DatabaseManager()
    db_manager.initialize()

    user_manager = UserManager(db_manager)
    user = user_manager.authenticate_user(username, master_password)
    if user is None:
        db_manager.close()
        raise click.ClickException("Invalid username or password.")

    master_key_data = db_manager.get_master_key(user_id=user.id)
    if master_key_data:
        _, salt_hex = master_key_data
        salt = bytes.fromhex(salt_hex)
    else:
        salt = _secrets.token_bytes(16)
        dummy_hash, _ = CryptoManager.hash_password(master_password)
        db_manager.save_master_key(dummy_hash, salt.hex(), user_id=user.id)

    crypto_manager = CryptoManager(master_password, salt=salt)
    vault_manager = VaultManager(crypto_manager, db_manager, user_id=user.id)
    return vault_manager, crypto_manager, db_manager


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Password Manager - Secure password storage and management."""
    ctx.ensure_object(dict)
    settings = get_settings()
    ctx.obj["settings"] = settings


@cli.command()
@click.option("--length", "-l", default=16, help="Password length")
@click.option("--no-special", is_flag=True, help="Exclude special characters")
@click.option("--passphrase", is_flag=True, help="Generate passphrase instead")
@click.pass_context
def generate(
    ctx: click.Context, length: int, no_special: bool, passphrase: bool
) -> None:
    """Generate a secure password."""
    if passphrase:
        generator = PasswordGenerator()
        password = generator.generate_passphrase()
    else:
        generator = PasswordGenerator(length=length, use_special=not no_special)
        password = generator.generate()

    strength = PasswordGenerator.calculate_strength(password)
    click.echo(f"Generated Password: {password}")
    click.echo(f"Strength: {strength.name}")


@cli.command()
@click.argument("password")
@click.pass_context
def strength(ctx: click.Context, password: str) -> None:
    """Check password strength."""
    strength_level = PasswordGenerator.calculate_strength(password)
    click.echo(f"Password Strength: {strength_level.name}")


@cli.group()
@click.pass_context
def vault(ctx: click.Context) -> None:
    """Manage password vault."""
    pass


@vault.command()
@click.option("--title", "-t", required=True, help="Entry title")
@click.option("--username", "-u", required=True, help="Username")
@click.option("--password", "-p", help="Password (will prompt if not provided)")
@click.option("--url", help="Website URL")
@click.option("--category", "-c", help="Category")
@click.option("--tags", help="Comma-separated tags")
@click.pass_context
def add(
    ctx: click.Context,
    title: str,
    username: str,
    password: Optional[str],
    url: Optional[str],
    category: Optional[str],
    tags: Optional[str],
) -> None:
    """Add a new password entry."""
    if password is None:
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    try:
        vault_manager, crypto_manager, db_manager = _get_authenticated_vault(ctx)

        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        entry = vault_manager.add_entry(
            title=title,
            username=username,
            password=password,
            url=url,
            category=category,
            tags=tag_list,
        )

        click.echo(f"✓ Entry added successfully (ID: {entry.id})")

        crypto_manager.clear_key()
        db_manager.close()

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()


@vault.command("list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--search", "-s", help="Search query")
@click.pass_context
def list_entries(
    ctx: click.Context, category: Optional[str], tag: Optional[str], search: Optional[str]
) -> None:
    """List password entries."""
    try:
        vault_manager, crypto_manager, db_manager = _get_authenticated_vault(ctx)

        entries = vault_manager.list_entries(category=category, tag=tag, search=search)

        if not entries:
            click.echo("No entries found.")
            crypto_manager.clear_key()
            db_manager.close()
            return

        click.echo(f"\nFound {len(entries)} entries:\n")
        for entry in entries:
            click.echo(f"ID: {entry.id}")
            click.echo(f"  Title: {entry.title}")
            click.echo(f"  Username: {entry.username}")
            if entry.url:
                click.echo(f"  URL: {entry.url}")
            if entry.category:
                click.echo(f"  Category: {entry.category}")
            click.echo()

        crypto_manager.clear_key()
        db_manager.close()

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()


@vault.command()
@click.argument("entry_id", type=int)
@click.pass_context
def get(ctx: click.Context, entry_id: int) -> None:
    """Get password entry by ID."""
    try:
        vault_manager, crypto_manager, db_manager = _get_authenticated_vault(ctx)

        entry = vault_manager.get_entry(entry_id)
        if entry is None:
            click.echo(f"Entry with ID {entry_id} not found.")
            crypto_manager.clear_key()
            db_manager.close()
            return

        decrypted_password = vault_manager.get_decrypted_password(entry_id)

        click.echo(f"\nEntry ID: {entry.id}")
        click.echo(f"Title: {entry.title}")
        click.echo(f"Username: {entry.username}")
        click.echo(f"Password: {decrypted_password}")
        if entry.url:
            click.echo(f"URL: {entry.url}")
        if entry.notes:
            click.echo(f"Notes: {entry.notes}")
        if entry.category:
            click.echo(f"Category: {entry.category}")
        if entry.tags:
            click.echo(f"Tags: {', '.join(entry.tags)}")

        crypto_manager.clear_key()
        db_manager.close()

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()


@vault.command()
@click.argument("entry_id", type=int)
@click.option("--title", "-t", help="New title")
@click.option("--username", "-u", help="New username")
@click.option("--password", "-p", help="New password")
@click.option("--url", help="New URL")
@click.option("--category", "-c", help="New category")
@click.pass_context
def update(
    ctx: click.Context,
    entry_id: int,
    title: Optional[str],
    username: Optional[str],
    password: Optional[str],
    url: Optional[str],
    category: Optional[str],
) -> None:
    """Update password entry."""
    try:
        vault_manager, crypto_manager, db_manager = _get_authenticated_vault(ctx)

        entry = vault_manager.update_entry(
            entry_id=entry_id,
            title=title,
            username=username,
            password=password,
            url=url,
            category=category,
        )

        if entry is None:
            click.echo(f"Entry with ID {entry_id} not found.")
            crypto_manager.clear_key()
            db_manager.close()
            return

        click.echo(f"��� Entry {entry_id} updated successfully")

        crypto_manager.clear_key()
        db_manager.close()

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()


@vault.command()
@click.argument("entry_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this entry?")
@click.pass_context
def delete(ctx: click.Context, entry_id: int) -> None:
    """Delete password entry."""
    try:
        vault_manager, crypto_manager, db_manager = _get_authenticated_vault(ctx)

        success = vault_manager.delete_entry(entry_id)

        if success:
            click.echo(f"✓ Entry {entry_id} deleted successfully")
        else:
            click.echo(f"Entry with ID {entry_id} not found.")

        crypto_manager.clear_key()
        db_manager.close()

    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize the password vault."""
    click.echo("Initializing Password Manager...")

    try:
        db_manager = DatabaseManager()
        db_manager.initialize()
        click.echo("✓ Database initialized successfully")

        username = click.prompt("Set Username")
        master_password = click.prompt(
            "Set Master Password", hide_input=True, confirmation_prompt=True
        )

        user_manager = UserManager(db_manager)
        user = user_manager.create_user(username, master_password)

        crypto_manager = CryptoManager(master_password)
        hashed_key, _ = CryptoManager.hash_password(master_password)
        db_manager.save_master_key(hashed_key, crypto_manager.salt.hex(), user_id=user.id)

        click.echo(f"✓ User '{username}' created and master password set successfully")
        click.echo("\nPassword Manager is ready to use!")

        crypto_manager.clear_key()
        db_manager.close()

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()