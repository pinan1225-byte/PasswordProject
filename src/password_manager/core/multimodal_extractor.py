"""Multimodal text extractor supporting OCR (Image to Text) and ASR (Audio to Text)."""

import os
import platform
import shutil
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)


class MultimodalExtractor:
    """Extract text from images (OCR) and audio (ASR) with resilient system fallbacks."""

    @staticmethod
    def extract_text_from_image(image_path: str) -> str:
        """
        Extract text from an image using local OCR libraries or macOS Vision.

        Args:
            image_path: Absolute path to the image file.

        Returns:
            Extracted text string.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # 1. 尝试使用 easyocr (若可用)
        try:
            import easyocr
            logger.info("Using easyocr for image text extraction.")
            reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
            results = reader.readtext(image_path)
            extracted = "\n".join([r[1] for r in results])
            if extracted.strip():
                return extracted
        except (ImportError, Exception) as e:
            logger.debug("Local easyocr unavailable or failed: %s. Falling back to native.", e)

        # 2. 针对 macOS，使用 Swift 脚本直接调用系统 Vision 框架原生 OCR
        if platform.system() == "Darwin" and shutil.which("swift"):
            logger.info("Using macOS native Vision framework via Swift for OCR.")
            swift_ocr_code = """
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count > 1 else { exit(1) }
let imagePath = CommandLine.arguments[1]
let imageUrl = URL(fileURLWithPath: imagePath)

guard let image = NSImage(contentsOf: imageUrl),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    exit(1)
}

let requestHandler = VNImageRequestHandler(cgImage: cgImage, options: [:])
let request = VNRecognizeTextRequest { (request, error) in
    guard error == nil,
          let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for observation in observations {
        if let topCandidate = observation.topCandidates(1).first {
            print(topCandidate.string)
        }
    }
}

request.recognitionLanguages = ["zh-Hans", "en-US"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false

do {
    try requestHandler.perform([request])
} catch {
    exit(1)
}
"""
            with tempfile.NamedTemporaryFile(suffix=".swift", mode="w", delete=False) as f:
                f.write(swift_ocr_code)
                temp_swift = f.name

            try:
                result = subprocess.run(
                    ["swift", temp_swift, image_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                output = result.stdout.strip()
                if output:
                    return output
            except Exception as se:
                logger.warning("macOS Swift Vision OCR failed: %s", se)
            finally:
                if os.path.exists(temp_swift):
                    os.remove(temp_swift)

        # 3. 兜底方案：返回空，由 UI 引导用户确认
        logger.warning("No OCR extraction method succeeded for image: %s", image_path)
        return ""

    @staticmethod
    def extract_text_from_audio(audio_path: str) -> str:
        """
        Extract text from an audio file using local ASR libraries or macOS Speech.

        Args:
            audio_path: Absolute path to the audio file.

        Returns:
            Extracted text string.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 0. 优先尝试使用大模型/OpenAI Whisper 接口进行高精确度转录
        try:
            from src.password_manager.core.llm_client import LLMClient
            logger.info("Attempting online Whisper ASR transcription...")
            llm_client = LLMClient()
            client = llm_client.client
            if client:
                with open(audio_path, "rb") as audio_file:
                    # 使用标准 whisper-1 模型提取文字
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                extracted = transcript.text
                if extracted.strip():
                    logger.info("Online Whisper ASR transcription succeeded.")
                    return extracted
        except Exception as we:
            logger.warning("Online Whisper ASR failed or unsupported: %s. Falling back to local channels.", we)

        # 1. 尝试使用 SpeechRecognition (若可用)
        try:
            import speech_recognition as sr
            logger.info("Using SpeechRecognition library for audio transcription.")
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio_data = r.record(source)
            # 尝试使用 Google 或者是离线 Sphinx 进行语音识别
            try:
                extracted = r.recognize_google(audio_data, language="zh-CN")
                if extracted.strip():
                    return extracted
            except Exception as re:
                logger.warning("Google Speech Recognition failed: %s. Trying other channels.", re)
                # 尝试 PocketSphinx 离线识别
                extracted = r.recognize_sphinx(audio_data, language="zh-CN")
                if extracted.strip():
                    return extracted
        except (ImportError, Exception) as e:
            logger.debug("SpeechRecognition library unavailable or failed: %s. Falling back to native.", e)

        # 2. 针对 macOS，使用 Swift 脚本直接调用系统 Speech 框架原生 ASR (支持离线/在线识别)
        if platform.system() == "Darwin" and shutil.which("swift"):
            logger.info("Using macOS native Speech framework via Swift for ASR.")
            swift_asr_code = """
import Foundation
import Speech

guard CommandLine.arguments.count > 1 else { exit(1) }
let audioPath = CommandLine.arguments[1]
let audioUrl = URL(fileURLWithPath: audioPath)

// 请求麦克风/听写相关权限许可（针对沙盒应用）
let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))
guard recognizer?.isAvailable == true else {
    exit(1)
}

let request = SFSpeechURLRecognitionRequest(url: audioUrl)
let semaphore = DispatchSemaphore(value: 0)

recognizer?.recognizeTask(with: request) { (result, error) in
    if error != nil {
        semaphore.signal()
        return
    }
    if let result = result {
        if result.isFinal {
            print(result.bestTranscription.formattedString)
            semaphore.signal()
        }
    }
}

_ = semaphore.wait(timeout: .now() + 15.0)
"""
            with tempfile.NamedTemporaryFile(suffix=".swift", mode="w", delete=False) as f:
                f.write(swift_asr_code)
                temp_swift = f.name

            try:
                result = subprocess.run(
                    ["swift", temp_swift, audio_path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                output = result.stdout.strip()
                if output:
                    return output
            except Exception as se:
                logger.warning("macOS Swift Speech ASR failed: %s", se)
            finally:
                if os.path.exists(temp_swift):
                    os.remove(temp_swift)

        # 3. 兜底方案
        logger.warning("No ASR extraction method succeeded for audio: %s", audio_path)
        return ""
