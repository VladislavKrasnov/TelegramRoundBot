import asyncio
import os
import logging

logger = logging.getLogger(__name__)

async def get_video_duration(input_path: str) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_message = stderr.decode().strip()
        logger.error(f"ffprobe error: {error_message}")
        raise RuntimeError(f"Failed to get video duration: {error_message}")
    
    return float(stdout.decode().strip())

async def process_video(input_path: str, output_path: str):
    try:
        duration = await get_video_duration(input_path)
        filters = (
            r"crop=min(iw\,ih):min(iw\,ih):"
            r"(iw-min(iw\,ih))/2:(ih-min(iw\,ih))/2,"
            "scale=640:640"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", filters,
            "-preset", "fast",
            "-threads", "0",
            "-crf", "23",
            "-c:a", "aac",
            "-movflags", "+faststart",
            "-loglevel", "error"
        ]

        if duration > 60:
            cmd.insert(cmd.index("-i") + 2, "-t")
            cmd.insert(cmd.index("-t") + 1, "60")

        cmd.append(output_path)
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr_data = await proc.communicate()

        if proc.returncode != 0:
            error_message = stderr_data.decode().strip()
            logger.error(f"FFmpeg error: {error_message}")
            raise RuntimeError(f"Video processing failed: {error_message}")

        file_size = os.path.getsize(output_path)
        if file_size > 20 * 1024 * 1024:
            raise ValueError(f"File too big: {file_size // 1024 // 1024}MB")

    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        raise
