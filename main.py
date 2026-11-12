import json
import time
import re

# -----------------------------------------------------------------------------
# 1. 상수 및 라벨 정규화
# -----------------------------------------------------------------------------
EPSILON = 1e-9  # 부동소수점 동점 판정 허용 오차


def normalize_label(label: str) -> str:
    """
    입력된 라벨을 프로그램 표준 라벨('Cross' 또는 'X')로 정규화합니다.
    """
    if not isinstance(label, str):
        return str(label)
    
    cleaned = label.strip().lower()
    if cleaned in ['+', 'cross', '십자가']:
        return 'Cross'
    elif cleaned in ['x', 'cross_x', 'x_mark']:
        return 'X'
    return label.capitalize()


# -----------------------------------------------------------------------------
# 2. 순수 반복문 기반 MAC 연산 엔진 (외부 라이브러리 금지)
# -----------------------------------------------------------------------------
def mac_2d(matrix_a: list, matrix_b: list) -> float:
    """
    입력 패턴과 필터를 위치별로 곱하고 모두 더하는 연산을 수행합니다.
    """
    n = len(matrix_a)
    score = 0.0
    for r in range(n):
        for c in range(n):
            score += float(matrix_a[r][c]) * float(matrix_b[r][c])
    return score


def measure_mac_time(matrix_a: list, matrix_b: list, iterations: int = 10) -> float:
    """
    I/O 시간을 제외하고 순수 MAC 연산 함수 호출 구간만 10회 반복 측정하여 평균(ms)을 반환합니다.
    """
    start_t = time.perf_counter()
    for _ in range(iterations):
        mac_2d(matrix_a, matrix_b)
    end_t = time.perf_counter()
    return ((end_t - start_t) / iterations) * 1000


# -----------------------------------------------------------------------------
# 3. Epsilon 기반 점수 비교 및 판정 로직
# -----------------------------------------------------------------------------
def evaluate_decision(score_a: float, score_b: float, label_a: str = "Cross", label_b: str = "X") -> str:
    """
    허용오차(epsilon) 정책을 적용하여 두 점수를 비교하고 판정 결과를 반환합니다.
    """
    diff = score_a - score_b
    if abs(diff) < EPSILON:
        return "UNDECIDED"
    elif diff > 0:
        return label_a
    else:
        return label_b


# -----------------------------------------------------------------------------
# 4. 모드 1: 사용자 입력 처리 및 실행 (3x3)
# -----------------------------------------------------------------------------
def input_matrix(size: int, name: str) -> list:
    """
    n x n 크기의 행렬을 한 줄씩(공백 구분) 입력받으며 오류 시 재입력을 유도합니다.
    """
    print(f"\n{name} ({size}줄 입력, 공백 구분)")
    while True:
        matrix = []
        error_occurred = False
        for _ in range(size):
            line = input().strip()
            tokens = line.split()
            if len(tokens) != size:
                print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                error_occurred = True
                break
            try:
                row = [float(t) for t in tokens]
                matrix.append(row)
            except ValueError:
                print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                error_occurred = True
                break
        
        if not error_occurred:
            return matrix


def run_mode_1():
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")
    filter_a = input_matrix(3, "필터 A")
    filter_b = input_matrix(3, "필터 B")
    
    # 실행 흐름 요구사항: 필터 저장 확인
    print("\n✓ 필터 A (3x3), 필터 B (3x3) 저장이 완료되었습니다.")

    print("\n#----------------------------------------")
    print("# [2] 패턴 입력")
    print("#----------------------------------------")
    pattern = input_matrix(3, "패턴")

    # MAC 연산 수행 및 10회 반복 성능 측정
    score_a = mac_2d(pattern, filter_a)
    score_b = mac_2d(pattern, filter_b)
    
    time_a = measure_mac_time(pattern, filter_a, iterations=10)
    time_b = measure_mac_time(pattern, filter_b, iterations=10)
    avg_time_ms = (time_a + time_b) / 2

    # 모드 1에서는 필터 A, B로 판정
    decision = evaluate_decision(score_a, score_b, label_a="A", label_b="B")

    print("\n#----------------------------------------")
    print("# [3] MAC 결과 및 판정")
    print("#----------------------------------------")
    print(f"A 점수: {score_a:.16f}".rstrip('0').rstrip('.'))
    print(f"B 점수: {score_b:.16f}".rstrip('0').rstrip('.'))
    if decision == "UNDECIDED":
        print(f"판정: UNDECIDED (|A-B| < {EPSILON})")
    else:
        print(f"판정: {decision}")

    # 실행 흐름 요구사항: 성능 분석(3x3) 출력
    print("\n#----------------------------------------")
    print("# [4] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    print(f"{'크기(N×N)':<12} {'평균 시간(ms)':<16} {'연산 횟수(N²)':<12}")
    print("-" * 44)
    print(f"{'3×3':<12} {avg_time_ms:<16.4f} {9:<12}")


# -----------------------------------------------------------------------------
# 5. 모드 2: data.json 로드 및 검증/분석
# -----------------------------------------------------------------------------
def run_mode_2(json_path: str = "data.json"):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"\n[오류] '{json_path}' 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError as e:
        print(f"\n[오류] JSON 파싱 실패: {e}")
        return

    filters_raw = data.get("filters", {})
    patterns_raw = data.get("patterns", {})

    # 1. 필터 로드 및 라벨 정규화
    print("\n#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")
    loaded_filters = {}

    for f_key, f_val in filters_raw.items():
        try:
            size = int(f_key.split('_')[1])
        except (IndexError, ValueError):
            continue
        
        loaded_filters[size] = {}
        for sub_k, sub_v in f_val.items():
            norm_k = normalize_label(sub_k)
            loaded_filters[size][norm_k] = sub_v
        
        available_labels = ", ".join(loaded_filters[size].keys())
        print(f"✓ {f_key:<8} 필터 로드 완료 ({available_labels})")

    # 2. 패턴 로드/검증 및 MAC 연산/판정
    print("\n#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    fail_details = []
    perf_records = {}

    for p_key, p_val in patterns_raw.items():
        total_tests += 1
        print(f"-- {p_key} ---")

        match = re.search(r'size_(\d+)', p_key)
        if not match:
            msg = f"키 형식 오류: 크기를 추출할 수 없음 ('{p_key}')"
            print(f"판정: FAIL ({msg})\n")
            failed_tests += 1
            fail_details.append((p_key, msg))
            continue

        n = int(match.group(1))
        input_matrix_data = p_val.get("input", [])
        expected = normalize_label(p_val.get("expected", ""))

        # 스키마 및 크기 검증 (불일치 시 프로그램 중단 없이 FAIL 처리)
        if n not in loaded_filters:
            msg = f"{n}×{n} 크기 필터 미존재"
            print(f"판정: FAIL ({msg})\n")
            failed_tests += 1
            fail_details.append((p_key, msg))
            continue

        row_cnt = len(input_matrix_data)
        col_cnt = len(input_matrix_data[0]) if row_cnt > 0 else 0
        if row_cnt != n or col_cnt != n or any(len(r) != n for r in input_matrix_data):
            msg = f"크기 불일치 (패턴 {row_cnt}×{col_cnt} vs 필터 {n}×{n})"
            print(f"판정: FAIL ({msg})\n")
            failed_tests += 1
            fail_details.append((p_key, msg))
            continue

        filter_cross = loaded_filters[n].get("Cross")
        filter_x = loaded_filters[n].get("X")

        if not filter_cross or not filter_x:
            msg = f"{n}×{n} 필터(Cross/X) 구성 누락"
            print(f"판정: FAIL ({msg})\n")
            failed_tests += 1
            fail_details.append((p_key, msg))
            continue

        # MAC 연산 및 시간 측정
        score_cross = mac_2d(input_matrix_data, filter_cross)
        score_x = mac_2d(input_matrix_data, filter_x)
        avg_time_ms = measure_mac_time(input_matrix_data, filter_cross, iterations=10)

        if n not in perf_records:
            perf_records[n] = []
        perf_records[n].append(avg_time_ms)

        # Epsilon 판정 및 PASS/FAIL 비교
        decision = evaluate_decision(score_cross, score_x, label_a="Cross", label_b="X")

        print(f"Cross 점수: {score_cross:.16f}".rstrip('0').rstrip('.'))
        print(f"X 점수    : {score_x:.16f}".rstrip('0').rstrip('.'))

        if decision == expected:
            print(f"판정: {decision} | expected: {expected} | PASS\n")
            passed_tests += 1
        else:
            fail_reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL" if decision == "UNDECIDED" else f"예상 값('{expected}')과 불일치"
            print(f"판정: {decision} | expected: {expected} | FAIL ({fail_reason})\n")
            failed_tests += 1
            fail_details.append((p_key, fail_reason))

    # 3. 성능 분석 출력 (3x3 포함, 5x5/13x13/25x25 출력)
    print("\n#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    
    # data.json에 3x3 데이터가 없을 경우 기준 측정을 위해 기본 3x3 데이터로 측정 추가
    if 3 not in perf_records:
        base_3x3 = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
        perf_records[3] = [measure_mac_time(base_3x3, base_3x3, iterations=10)]

    print(f"{'크기(N×N)':<12} {'평균 시간(ms)':<16} {'연산 횟수(N²)':<12}")
    print("-" * 44)
    
    for size in sorted(perf_records.keys()):
        times = perf_records[size]
        avg_time = sum(times) / len(times)
        op_count = size * size
        size_label = f"{size}×{size}"
        print(f"{size_label:<12} {avg_time:<16.4f} {op_count:<12}")

    # 4. 결과 요약 출력
    print("\n#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print(f"총 테스트: {total_tests}개")
    print(f"통과: {passed_tests}개")
    print(f"실패: {failed_tests}개")

    if failed_tests > 0:
        print("\n실패 케이스:")
        for item_id, reason in fail_details:
            print(f"{item_id}: {reason}")


# -----------------------------------------------------------------------------
# 6. 메인 실행 흐름
# -----------------------------------------------------------------------------
def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    
    choice = input("선택: ").strip()
    if choice == '1':
        run_mode_1()
    elif choice == '2':
        run_mode_2()
    else:
        print("올바르지 않은 선택입니다. 프로그램을 종료합니다.")


if __name__ == "__main__":
    main()