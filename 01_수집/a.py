#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
rule.khu.ac.kr 자동 다운로드 스크립트 (개선버전)
- 여러 파일 다운로드 팝업 자동허용 (Chrome prefs)
- 파일 다운로드 경로 = 파이썬 실행 폴더
- 크롬 브라우저 띄우기 (Selenium)
- 1290 ~ 3000년까지 fileDown(year, 'ori') 호출
- JS alert 발생 시 자동 확인
- logging + tqdm
"""

import os
import time
import logging
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException,
    WebDriverException,
)

# ===================================================================
# 1. 설정
# ===================================================================

URL = "https://rule.khu.ac.kr/lmxsrv/law/lawListManager.do?SEQ=2&LAWGROUP=1&PAGE=1"

START_YEAR = 0
END_YEAR = 3000
DELAY_BETWEEN = 0.30  # 초

CHROMEDRIVER_PATH = None  # None이면 PATH 검색
LOG_FILE = "khu_downloader.log"

# 다운로드 저장 폴더 = 현재 작업 폴더
download_dir = os.getcwd()


# ===================================================================
# 2. 로깅 설정
# ===================================================================

logger = logging.getLogger("khu_downloader")
logger.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)

fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setFormatter(fmt)
logger.addHandler(fh)

logger.info("=== KHU 규정집 자동 다운로드 시작 ===")


# ===================================================================
# 3. 크롬 드라이버 생성 (다운로드 자동허용 포함)
# ===================================================================

def create_driver():

    chrome_options = Options()

    # 여러 파일 다운로드 자동 허용 + 다운로드 경로 설정
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,   # 다운로드 팝업 차단
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        # 여러 파일 다운로드 보안 팝업 자동 허용
        "profile.default_content_setting_values.automatic_downloads": 1
    }

    chrome_options.add_experimental_option("prefs", prefs)

    # 팝업/알림 차단
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    # 필요하면 headless
    # chrome_options.add_argument("--headless=new")

    if CHROMEDRIVER_PATH:
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    driver.maximize_window()

    return driver


driver = create_driver()

logger.info(f"접속 중: {URL}")
driver.get(URL)

time.sleep(2.0)


# ===================================================================
# 4. fileDown 함수 존재 확인
# ===================================================================

def wait_for_fileDown(timeout=10):
    logger.info("fileDown 함수 로딩 대기...")
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            exists = driver.execute_script("return (typeof fileDown === 'function');")
            if exists:
                logger.info("fileDown 함수 확인 완료.")
                return True
        except WebDriverException:
            pass

        time.sleep(0.5)

    logger.warning("fileDown 함수를 찾지 못했습니다.")
    return False


wait_for_fileDown()


# ===================================================================
# 5. alert 자동 처리 함수
# ===================================================================

def handle_alert(max_wait=1.5):

    try:
        WebDriverWait(driver, max_wait).until(EC.alert_is_present())
    except TimeoutException:
        return False

    try:
        alert = driver.switch_to.alert
        text = alert.text
        logger.warning(f"[ALERT] '{text}' -> 자동확인")
        alert.accept()
        return True

    except Exception:
        return False


# ===================================================================
# 6. 메인 루프
# ===================================================================

failed_years = []

for year in tqdm(range(START_YEAR, END_YEAR + 1), desc="Downloading", ncols=100):

    year_str = str(year)

    try:
        # 자바스크립트 호출
        driver.execute_script("fileDown(arguments[0], 'ori');", year_str)
        logger.info(f"[시도] {year_str}/{END_YEAR}")

        # alert 발생시 자동 처리
        if handle_alert(max_wait=1.5):
            failed_years.append(year)

    except WebDriverException as e:
        logger.error(f"[에러] {year_str}년: {e}")
        failed_years.append(year)

    time.sleep(DELAY_BETWEEN)

logger.info("=== 다운로드 루프 종료 ===")

if failed_years:
    logger.warning(f"실패 연도 ({len(failed_years)}개): {failed_years}")
else:
    logger.info("모든 파일 성공 또는 alert 없이 완료")

driver.quit()
logger.info("드라이버 종료. 스크립트 끝.")
