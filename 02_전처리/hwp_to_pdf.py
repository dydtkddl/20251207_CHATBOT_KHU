#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HWP / HWPX → PDF 대량 변환 스크립트

- 지정한 루트 폴더에서 .hwp, .hwpx 파일을 재귀적으로 모두 찾는다.
- LibreOffice(soffice)를 headless 모드로 호출해서 PDF로 변환한다.
- logging + tqdm 으로 진행 상황 및 에러를 기록한다.

필수:
- LibreOffice 설치
- SOFFICE_PATH 를 OS 환경에 맞게 설정
"""

import os
import subprocess
import logging
from pathlib import Path
from tqdm import tqdm

# ============================================================
# 1. 설정
# ============================================================

# 변환할 HWP/HWPX 가 들어 있는 루트 디렉토리
INPUT_DIR = Path(r"./hwp_input")

# PDF 결과를 저장할 디렉토리
OUTPUT_DIR = Path(r"./pdf_output")

# LibreOffice 실행 파일 경로
# - Windows 예: r"C:\Program Files\LibreOffice\program\soffice.exe"
# - Linux/macOS 예: "soffice"  (PATH 에 잡혀 있다면)
SOFFICE_PATH = r"soffice"

# 로그 파일 이름
LOG_FILE = "hwp_to_pdf_batch.log"


# ============================================================
# 2. 로깅 설정
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# 3. 유틸 함수들
# ============================================================

def find_hwp_files(root: Path):
    """
    root 이하에서 .hwp, .hwpx 파일을 모두 찾아 리스트로 반환.
    """
    exts = {".hwp", ".hwpx"}
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return files


def convert_hwp_to_pdf(hwp_path: Path, out_dir: Path) -> bool:
    """
    단일 HWP/HWPX 파일을 PDF로 변환.
    - 성공하면 True, 실패하면 False 반환.
    - LibreOffice의 'soffice --headless --convert-to pdf' 사용.
    """
    # 출력 디렉토리 존재 보장
    out_dir.mkdir(parents=True, exist_ok=True)

    # LibreOffice CLI 명령
    cmd = [
        SOFFICE_PATH,
        "--headless",
        "--norestore",
        "--invisible",
        "--convert-to", "pdf",
        "--outdir", str(out_dir),
        str(hwp_path)
    ]

    try:
        # stdout/stderr 는 로그 확인용으로만 가져오고 화면엔 띄우지 않음
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"[OK] {hwp_path} → PDF 변환 완료")
        if result.stdout:
            logger.debug(f"LibreOffice stdout: {result.stdout.strip()}")
        if result.stderr:
            logger.debug(f"LibreOffice stderr: {result.stderr.strip()}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"[FAIL] {hwp_path} 변환 실패 (returncode={e.returncode})")
        if e.stdout:
            logger.error(f"stdout: {e.stdout.strip()}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr.strip()}")
        return False

    except FileNotFoundError:
        logger.critical(
            f"LibreOffice 실행 파일({SOFFICE_PATH})을 찾을 수 없습니다. "
            f"SOFFICE_PATH 설정을 확인하세요."
        )
        # 이 경우는 치명적이라 False 를 넘기지만, 실제론 스크립트 종료를 고려해도 됨.
        return False

    except Exception as e:
        logger.exception(f"[EXCEPTION] {hwp_path} 변환 중 예외 발생: {e}")
        return False


# ============================================================
# 4. 메인 루틴
# ============================================================

def main():
    logger.info("============================================")
    logger.info("HWP / HWPX → PDF 대량 변환 시작")
    logger.info(f"입력 폴더 : {INPUT_DIR.resolve()}")
    logger.info(f"출력 폴더 : {OUTPUT_DIR.resolve()}")
    logger.info(f"soffice 경로 : {SOFFICE_PATH}")
    logger.info("============================================")

    if not INPUT_DIR.exists():
        logger.error(f"입력 폴더가 존재하지 않습니다: {INPUT_DIR}")
        return

    # 변환 대상 HWP/HWPX 파일들 수집
    hwp_files = find_hwp_files(INPUT_DIR)
    total = len(hwp_files)

    if total == 0:
        logger.warning("변환할 HWP/HWPX 파일이 없습니다.")
        return

    logger.info(f"총 변환 대상 파일 수: {total}")

    success_count = 0
    fail_count = 0

    # tqdm 진행률 표시
    for hwp_path in tqdm(hwp_files, desc="HWP → PDF", unit="file"):
        ok = convert_hwp_to_pdf(hwp_path, OUTPUT_DIR)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    logger.info("============================================")
    logger.info(f"변환 완료: 총 {total}개 중 성공 {success_count}개, 실패 {fail_count}개")
    logger.info("로그 파일: %s", os.path.abspath(LOG_FILE))
    logger.info("============================================")


if __name__ == "__main__":
    main()
