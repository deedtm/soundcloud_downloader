import os
import random
import shutil
import subprocess
import time
from os import path as p

TRACKS_FILE = "tracks.txt"
TRACKS_DIR = "tracks"
OUTPUT_DIR = "downloads"
MISC_OUTPUT = "MISC"
ARCHIVE_NAME = OUTPUT_DIR
ARCHIVE_FORMAT = "zip"  # "tar", "gztar"

# диапазон случайной задержки между запросами в секундах
RATE_LIMIT_RANGE = (1.0, 2.0)


def create_output_dirs():
    performers = [d for d in os.listdir(
        TRACKS_DIR) if p.isdir(p.join(TRACKS_DIR, d))]
    performers.sort()
    if MISC_OUTPUT in performers:
        performers.remove(MISC_OUTPUT)
        performers.append(MISC_OUTPUT)  # шоби последним был

    if not p.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for perf in performers:
        perf_dir = p.join(OUTPUT_DIR, perf)
        if not p.exists(perf_dir):
            os.makedirs(perf_dir)

    return performers


def parse_tracks(performers: list[str]):
    tracks = {perf: [] for perf in performers}
    for perf in performers:
        tracks_path = p.join(TRACKS_DIR, perf, TRACKS_FILE)
        try:
            with open(tracks_path) as f:
                content = f.read().strip().split('\n')
            if not content:
                print(
                    f"[!] отсутствуют треки для исполнителя `{perf}`, пропускаю...")
                continue
            tracks[perf].extend([l.strip() for l in content if l.strip()])
        except FileNotFoundError:
            print(
                f"[!] отсутствуют треки для исполнителя `{perf}`, пропускаю...")
    return tracks


def download_track(idx: int, total_tracks: int, output_dir: str, track: str):
    idx = str(idx).zfill(len(str(total_tracks)))
    out_template = p.join(output_dir, "%(title)s.%(ext)s")

    cmd = [
        "yt-dlp",
        f"scsearch1:{track}",
        "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", out_template,
        "--no-warnings",
        "--print", "after_move:filepath",
        "--sleep-requests", "1",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    ]

    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"
        )
        if result.returncode == 0:
            full_path = result.stdout.strip()
            filename = p.basename(full_path)
            print(
                f'[+] [{idx}/{total_tracks}] скачан трек `{track}`: {p.join(output_dir, filename)}')
            return True
        else:
            error_msg = result.stderr.strip().lstrip('ERROR: ')
            print(f"[!] [{idx}/{total_tracks}] ошибка: {error_msg[:256]}")

            print(
                f"[/] [{idx}/{total_tracks}] пробую скачать в дефолтном формате...")
            cmd_fallback = [
                cmd[0], cmd[1], "-x", "-o", out_template, "--no-warnings",
                "--print", "after_move:filepath", "--sleep-requests", "1", "--user-agent", cmd[11]
            ]
            result_fallback = subprocess.run(
                cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"
            )

            if result_fallback.returncode == 0:
                full_path = result_fallback.stdout.strip()
                filename = p.basename(full_path)
                print(
                    f'[+] [{idx}/{total_tracks}] скачан в исходном формате трек `{track}`: {p.join(output_dir, filename)}')
                return True
            else:
                error_msg = result.stderr.strip().lstrip('ERROR: ')
                print(
                    f"[!] [{idx}/{total_tracks}] ошибка скачивания трека `{track}`: {error_msg[:256]}")
                return False
    except Exception as e:
        print(
            f"[!] [{idx}/{total_tracks}] ошибка скачивания трека `{track}`: {e}")
        success = False

    if idx != str(total_tracks):
        sleep_time = random.uniform(*RATE_LIMIT_RANGE)
        time.sleep(sleep_time)

    return success


def download_performer_tracks(performer: str, tracks: list[str]):
    output_dir = p.join(OUTPUT_DIR, performer)
    total_tracks = len(tracks)
    successful = 0

    print(
        f'[/] скачиваю треки исполнителя: {performer} ({total_tracks} шт.)...')
    for idx, track in enumerate(tracks, 1):
        res = download_track(idx, total_tracks, output_dir,
                             f"{performer} - {track}")
        if res:
            successful += 1

    print(f'[#] {performer} — {successful}/{total_tracks} успешно скачано')


def download_misc_tracks(tracks: list[str]):
    output_dir = p.join(OUTPUT_DIR, MISC_OUTPUT)
    total_tracks = len(tracks)
    results = {}

    print(f'[/] скачиваю треки из общего файла ({total_tracks} шт.)...')
    for idx, track in enumerate(tracks, 1):
        res = download_track(idx, total_tracks, output_dir, track)
        results[res] = track
    print(
        f'[#] общий файл — {len(results.get(True, []))}/{len(results.get(False, []))} успешно/неуспешно скачано')


def main():
    if not p.exists(TRACKS_DIR) or not any(p.isdir(p.join(TRACKS_DIR, d)) for d in os.listdir(TRACKS_DIR)):
        print(f"[!] создай папку `{TRACKS_DIR}` и внутри создай папки под каждого исполнителя, а внутри папок исполнителей файл `{TRACKS_FILE}` с названиями треков для скачивания (желательный формат названий: Исполнитель - Название трека)")
        print(
            f'[=] совет: для треков, необязательно относящихся к определенному исполнителю, можно создать папку `{MISC_OUTPUT}` внутри папки `{TRACKS_DIR}` и в ней файл `{TRACKS_FILE}` с названиями треков')
        return

    if not TRACKS_FILE in os.listdir(TRACKS_DIR):
        print(
            f'[=] совет: для треков, необязательно относящихся к определенному исполнителю, можно создать внутри папки `{TRACKS_DIR}` папку `{MISC_OUTPUT}` и в ней файл `{TRACKS_FILE}` с названиями треков')
        print()

    print(f"[/] создаю папки для скачивания...")
    performers = create_output_dirs()
    print(f'[#] созданы папки: {", ".join(performers)}')

    print()

    print(f'[/] парсю треки из файлов...')
    tracks = parse_tracks(performers)
    print(f'[#] парсинг завершён. количество треков по папкам:')
    for perf, track_list in tracks.items():
        print(f'  {perf}: {len(track_list)}')

    print()

    print(f'[/] скачиваю треки...')
    for performer, track_list in tracks.items():
        if performer == MISC_OUTPUT:
            download_misc_tracks(track_list)
        else:
            download_performer_tracks(performer, track_list)
        print()
    print(f'[#] все скачивания завершены! проверь папку `{OUTPUT_DIR}`')

    print()

    print(f'[/] создаю архив содержимого папки `{OUTPUT_DIR}`: `{ARCHIVE_NAME}.{ARCHIVE_FORMAT}`...')
    try:
        shutil.make_archive(
            base_name=ARCHIVE_NAME,
            format=ARCHIVE_FORMAT,
            root_dir=OUTPUT_DIR,
            base_dir=os.curdir
        )
        print(f'[#] архив {ARCHIVE_NAME}.{ARCHIVE_FORMAT} создан!')
    except Exception as e:
        print(f'[!]не удалось создать архив: {e}')


if __name__ == "__main__":
    main()
