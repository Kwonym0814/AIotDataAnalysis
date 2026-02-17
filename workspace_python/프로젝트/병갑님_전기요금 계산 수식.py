


def add_electricity_cost_feature_B(
    df: pd.DataFrame,
    contract_kw: float = 660.0,
    basic_won_per_kw: float = 9810.0,
    pf_threshold: float = 90.0,
    pf_discount_mult: float = 0.98,  # PF >= 90% 할인
    pf_surcharge_mult: float = 1.02, # PF <  90% 할증
    apply_pf_to: str = "basic",      # "basic" (권장) | "total" | "energy"
) -> pd.DataFrame:
    df = df.copy()

    # 1) 날짜 파싱
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    if df["date"].isna().any():
        # 날짜 파싱 실패가 있으면 원인 확인이 필요하니 일단 그대로 두고 넘어감
        # (필요시 df[df["date"].isna()] 확인)
        pass

    df = df.sort_values("date")
    df["year_month"] = df["date"].dt.to_period("M")

    # 2) 계절
    m = df["date"].dt.month
    df["season"] = np.select(
        [m.isin([6, 7, 8]), m.isin([3, 4, 5, 9, 10])],
        ["summer", "spring_fall"],
        default="winter",
    )

    # 3) 시간대 (경/중/최대)
    hhmm = df["date"].dt.hour * 60 + df["date"].dt.minute
    offpeak = (hhmm >= 23 * 60) | (hhmm < 9 * 60)

    def in_range(x, sh, sm, eh, em):
        s = sh * 60 + sm
        e = eh * 60 + em
        return (x >= s) & (x < e)

    # 여름/봄가을
    mid_summer = (
        in_range(hhmm, 9, 0, 10, 0) |
        in_range(hhmm, 12, 0, 13, 0) |
        in_range(hhmm, 17, 0, 23, 0)
    )
    peak_summer = (
        in_range(hhmm, 10, 0, 12, 0) |
        in_range(hhmm, 13, 0, 17, 0)
    )

    mid_sf = mid_summer.copy()
    peak_sf = peak_summer.copy()

    # 겨울
    mid_winter = (
        in_range(hhmm, 9, 0, 10, 0) |
        in_range(hhmm, 12, 0, 17, 0) |
        in_range(hhmm, 20, 0, 22, 0)
    )
    peak_winter = (
        in_range(hhmm, 10, 0, 12, 0) |
        in_range(hhmm, 17, 0, 20, 0) |
        in_range(hhmm, 22, 0, 23, 0)
    )

    # 기본 mid -> offpeak -> peak 우선순위
    tou = np.full(len(df), "mid", dtype=object)
    tou[offpeak.values] = "offpeak"

    is_summer = df["season"].eq("summer").values
    is_sf = df["season"].eq("spring_fall").values
    is_winter = df["season"].eq("winter").values

    tou[np.where(is_summer & peak_summer.values)] = "peak"
    tou[np.where(is_sf & peak_sf.values)] = "peak"
    tou[np.where(is_winter & peak_winter.values)] = "peak"

    df["tou"] = tou

    # 4) 단가(원/kWh) — 선택(Ⅲ) 고압A
    price = {
        ("summer", "offpeak"): 55.2,
        ("summer", "mid"):     108.4,
        ("summer", "peak"):    178.7,
        ("spring_fall", "offpeak"): 55.2,
        ("spring_fall", "mid"):     77.3,
        ("spring_fall", "peak"):    101.0,
        ("winter", "offpeak"): 62.5,
        ("winter", "mid"):     108.6,
        ("winter", "peak"):    155.5,
    }

    # 벡터화 매핑
    key = list(zip(df["season"].values, df["tou"].values))
    df["unit_price_won_per_kwh"] = pd.Series(key, index=df.index).map(price).astype(float)

    df["energy_cost_won_15m"] = df["usage_kwh"] * df["unit_price_won_per_kwh"]

    # 5) 월 평균 역률 계산 (W, Wr 기반: usage_kwh, net kvarh)
    df["q_net_kvarh"] = (
        df["lagging_current_reactive_power_kvarh"]
        - df["leading_current_reactive_power_kvarh"]
    )

    W_month = df.groupby("year_month")["usage_kwh"].transform("sum")
    Wr_month = df.groupby("year_month")["q_net_kvarh"].transform("sum")

    denom = np.sqrt(W_month**2 + Wr_month**2)
    df["pf_month_pct"] = np.where(denom > 0, (W_month / denom) * 100.0, np.nan)

    # 6) PF 할인/할증 (90% 기준: 양쪽 모두 반영)
    df["pf_multiplier_month"] = np.where(
        df["pf_month_pct"] >= pf_threshold,
        pf_discount_mult,   # 할인
        pf_surcharge_mult,  # 할증
    )

    # 7) 기본요금(월) -> PF 적용 -> B안(usage 비례)으로 15분 배분
    monthly_basic_raw = contract_kw * basic_won_per_kw  # 월 총 기본요금(원), PF 전

    # 월별로 동일한 PF multiplier를 갖게 되므로, transform("first")로 안정적으로 가져옴
    pf_m = df.groupby("year_month")["pf_multiplier_month"].transform("first")

    monthly_basic_pf = monthly_basic_raw * pf_m  # PF 반영된 월 기본요금 총액(원)

    month_total_kwh = df.groupby("year_month")["usage_kwh"].transform("sum")
    df["basic_cost_won_15m"] = np.where(
        month_total_kwh > 0,
        monthly_basic_pf * (df["usage_kwh"] / month_total_kwh),
        0.0
    )

    # 8) 최종 비용 컬럼
    if apply_pf_to == "basic":
        # (권장) PF는 기본요금에만 반영됨. energy는 단가표 그대로.
        df["elec_cost_won_15m"] = df["energy_cost_won_15m"] + df["basic_cost_won_15m"]

    elif apply_pf_to == "energy":
        # PF를 전력량요금에만 적용하고 싶을 때
        df["elec_cost_won_15m"] = df["energy_cost_won_15m"] * pf_m + df["basic_cost_won_15m"]

    elif apply_pf_to == "total":
        # PF를 (energy + basic)에 통으로 적용하고 싶을 때
        df["elec_cost_won_15m"] = (df["energy_cost_won_15m"] + (contract_kw * basic_won_per_kw) * (df["usage_kwh"] / month_total_kwh)) * pf_m

    else:
        raise ValueError("apply_pf_to must be one of: 'basic', 'energy', 'total'")

    return df
	
out = add_electricity_cost_feature_B(dfaa, apply_pf_to="basic")

monthly_sum_basic = out.groupby("year_month")["basic_cost_won_15m"].sum()
monthly_pf = out.groupby("year_month")["pf_multiplier_month"].first()

print(pd.DataFrame({
    "basic_sum_krw": monthly_sum_basic,
    "pf_mult": monthly_pf
}).head(13))

out["pf_multiplier_month"].value_counts(dropna=False)

pf_monthly = out.groupby("year_month")["pf_month_pct"].first()
print(pf_monthly.describe())
print(pf_monthly.head(12))

