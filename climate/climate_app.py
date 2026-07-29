import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import plotly.graph_objects as go
import copy
from collections import defaultdict

# ==========================================
# 1. 页面基本配置与高级 UI 样式注入 (CSS)
# ==========================================
st.set_page_config(
    page_title="美国气候 analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #F4F7FC; }
    
    /* 顶部系统信息卡精细化 */
    .system-header {
        background-color: #FFFFFF; padding: 15px 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02); margin-bottom: 20px;
    }
    .system-title { font-size: 24px; font-weight: 800; color: #0F172A; margin: 0; }
    .system-subtitle { font-size: 12px; color: #64748B; margin-top: 4px; }
    .badge-tag { padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }
    
    /* 2列排版的天气卡片 */
    .weather-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0;
        border-radius: 16px; padding: 16px 20px; margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
    }
    .weather-card-today {
        background-color: #EFF6FF; border: 1.5px solid #2563EB;
        box-shadow: 0 4px 12px rgba(37,99,235,0.06);
    }
    
    /* 智能结论卡片样式 */
    .analysis-card {
        background-color: #FFFFFF; border: 1px solid #E2E8F0;
        border-radius: 12px; padding: 22px; margin-top: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# 2. 50个州首府城市坐标与区域
US_CAPITALS = {
    "Alabama (Montgomery)": {"lat": 32.377, "lon": -86.300, "region": "南大西洋/东南部"},
    "Alaska (Juneau)": {"lat": 58.301, "lon": -134.420, "region": "阿拉斯加"},
    "Arizona (Phoenix)": {"lat": 33.448, "lon": -112.074, "region": "西北/西南"},
    "Arkansas (Little Rock)": {"lat": 34.746, "lon": -92.289, "region": "南中央"},
    "California (Sacramento)": {"lat": 38.581, "lon": -121.494, "region": "太平洋"},
    "Colorado (Denver)": {"lat": 39.739, "lon": -104.990, "region": "山地"},
    "Connecticut (Hartford)": {"lat": 41.763, "lon": -72.685, "region": "新英格兰"},
    "Delaware (Dover)": {"lat": 39.158, "lon": -75.524, "region": "中大西洋"},
    "Florida (Tallahassee)": {"lat": 30.438, "lon": -84.280, "region": "南大西洋/东南部"},
    "Georgia (Atlanta)": {"lat": 33.749, "lon": -84.388, "region": "南大西洋/东南部"},
    "Hawaii (Honolulu)": {"lat": 21.306, "lon": -157.858, "region": "夏威夷"},
    "Idaho (Boise)": {"lat": 43.615, "lon": -116.202, "region": "西北/西南"},
    "Illinois (Springfield)": {"lat": 39.781, "lon": -89.650, "region": "西北中部"},
    "Indiana (Indianapolis)": {"lat": 39.768, "lon": -86.158, "region": "西北中部"},
    "Iowa (Des Moines)": {"lat": 41.600, "lon": -93.609, "region": "西北中部"},
    "Kansas (Topeka)": {"lat": 39.047, "lon": -95.675, "region": "西北中部"},
    "Kentucky (Frankfort)": {"lat": 38.200, "lon": -84.873, "region": "南中央"},
    "Louisiana (Baton Rouge)": {"lat": 30.451, "lon": -91.187, "region": "南中央"},
    "Maine (Augusta)": {"lat": 44.310, "lon": -69.779, "region": "新英格兰"},
    "Maryland (Annapolis)": {"lat": 38.978, "lon": -76.492, "region": "中大西洋"},
    "Massachusetts (Boston)": {"lat": 42.360, "lon": -71.058, "region": "新英格兰"},
    "Michigan (Lansing)": {"lat": 42.732, "lon": -84.555, "region": "东北中部"},
    "Minnesota (St. Paul)": {"lat": 44.953, "lon": -93.089, "region": "西北中部"},
    "Mississippi (Jackson)": {"lat": 32.298, "lon": -90.184, "region": "南中央"},
    "Missouri (Jefferson City)": {"lat": 38.576, "lon": -92.173, "region": "西北中部"},
    "Montana (Helena)": {"lat": 46.589, "lon": -112.039, "region": "山地"},
    "Nebraska (Lincoln)": {"lat": 40.825, "lon": -96.685, "region": "西北中部"},
    "Nevada (Carson City)": {"lat": 39.163, "lon": -119.767, "region": "山地"},
    "New Hampshire (Concord)": {"lat": 43.208, "lon": -71.537, "region": "新英格兰"},
    "New Jersey (Trenton)": {"lat": 40.217, "lon": -74.759, "region": "中大西洋"},
    "New Mexico (Santa Fe)": {"lat": 35.686, "lon": -105.937, "region": "西北/西南"},
    "New York (Albany)": {"lat": 42.652, "lon": -73.756, "region": "中大西洋"},
    "North Carolina (Raleigh)": {"lat": 35.779, "lon": -78.638, "region": "南大西洋/东南部"},
    "North Dakota (Bismarck)": {"lat": 46.808, "lon": -100.783, "region": "西北中部"},
    "Ohio (Columbus)": {"lat": 39.961, "lon": -82.998, "region": "东北中部"},
    "Oklahoma (Oklahoma)": {"lat": 35.467, "lon": -97.516, "region": "南中央"},
    "Oregon (Salem)": {"lat": 44.942, "lon": -123.035, "region": "太平洋"},
    "Pennsylvania (Harrisburg)": {"lat": 40.273, "lon": -76.886, "region": "中大西洋"},
    "Rhode Island (Providence)": {"lat": 41.824, "lon": -71.412, "region": "新英格兰"},
    "South Carolina (Columbia)": {"lat": 33.998, "lon": -81.034, "region": "南大西洋/东南部"},
    "South Dakota (Pierre)": {"lat": 44.368, "lon": -100.351, "region": "西北中部"},
    "Tennessee (Nashville)": {"lat": 36.162, "lon": -86.781, "region": "南中央"},
    "Texas (Austin)": {"lat": 30.267, "lon": -97.743, "region": "南中央"},
    "Utah (Salt Lake City)": {"lat": 40.760, "lon": -111.891, "region": "山地"},
    "Vermont (Montpelier)": {"lat": 44.260, "lon": -72.575, "region": "新英格兰"},
    "Virginia (Richmond)": {"lat": 37.540, "lon": -77.436, "region": "中大西洋"},
    "Washington (Olympia)": {"lat": 47.037, "lon": -122.900, "region": "太平洋"},
    "West Virginia (Charleston)": {"lat": 38.349, "lon": -81.632, "region": "中大西洋"},
    "Wisconsin (Madison)": {"lat": 43.073, "lon": -89.401, "region": "东北中部"},
    "Wyoming (Cheyenne)": {"lat": 41.140, "lon": -104.820, "region": "山地"}
}

# 跨页面统一选择状态源初始化
if "current_selected_states" not in st.session_state:
    st.session_state.current_selected_states = ["Alabama (Montgomery)"]

# ==========================================
# 3. 顶部信息卡 (优化标题)
# ==========================================
st.markdown("""
<div class="system-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span class="system-title">🌍 美国气候 analysis</span>
            <p class="system-subtitle">NWS 7-Day High-Precision & Open-Meteo Multi-Model Hybrid Engine • 级联双网气候决策系统</p>
        </div>
        <div style="display: flex; gap: 6px;">
            <span class="badge-tag" style="background-color: #EFF6FF; color: #1E40AF;">📅 实时双通道更新</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 侧边栏
st.sidebar.header("⚙️ 决策阈值")
temp_threshold = st.sidebar.slider(
    "冷暖区判定阈值设定 (°C)",
    min_value=10.0, max_value=25.0, value=16.0, step=0.5
)


# ==========================================
# 4. 数据仿真备用层（移除湿度、风速依赖）
# ==========================================
def generate_geographical_weather(lat, lon, seed_offset=0.0):
    base_temp = 35.0 - (abs(lat) - 25) * 0.7 + seed_offset
    base_temp = max(5.0, min(36.0, base_temp))
    
    seed_val = int(abs(lat + lon) * 100) + int(abs(seed_offset) * 10)
    np.random.seed(seed_val)
    
    max_temps = [round(base_temp + np.random.uniform(2, 6), 1) for _ in range(14)]
    min_temps = [round(base_temp - np.random.uniform(4, 8), 1) for _ in range(14)]
    precip = [int(np.random.uniform(5, 75)) for _ in range(14)]
    weather_codes = [int(np.random.choice([0, 1, 2, 3, 61])) for _ in range(14)]
    
    trend_vals = []
    current_val = base_temp
    for _ in range(5):
        current_val += np.random.uniform(-1.2, 1.2)
        trend_vals.append(round(current_val, 1))
        
    return {
        "time": [(datetime.date.today() + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14)],
        "temperature_2m_max": max_temps,
        "temperature_2m_min": min_temps,
        "precipitation_probability": precip,
        "weather_code": weather_codes,
        "weeks_trend": trend_vals,
        "is_simulated": True,
        "data_source": "Geographical Simulator"
    }


# ==========================================
# 5. 双引擎数据源之一：Open-Meteo (中长期趋势，HTTPS安全模式)
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_raw_api_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&timezone=auto&forecast_days=14"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    res = requests.get(url, headers=headers, timeout=5.0)
    if res.status_code == 200:
        return res.json()["daily"]
    raise RuntimeWarning(f"API returned status {res.status_code}")


def get_unified_weather(lat, lon):
    try:
        raw_data = fetch_raw_api_data(lat, lon)
        data = copy.deepcopy(raw_data)
        data["precipitation_probability"] = data.pop("precipitation_probability_max")
        
        means = [round((mx+mn)/2, 1) for mx, mn in zip(data["temperature_2m_max"], data["temperature_2m_min"])]
        
        w1 = round(np.mean(means[0:3]), 1)
        w2 = round(np.mean(means[3:7]), 1)
        w3 = round(np.mean(means[7:10]), 1)
        w4 = round(np.mean(means[10:14]), 1)
        w5 = round(w4 + np.random.uniform(-1.5, 1.5), 1)
        
        data["weeks_trend"] = [w1, w2, w3, w4, w5]
        data["is_simulated"] = False
        data["data_source"] = "Open-Meteo API"
        return data
    except Exception:
        return generate_geographical_weather(lat, lon)


def quick_check_temp(lat, lon):
    try:
        data = fetch_raw_api_data(lat, lon)
        mx = data["temperature_2m_max"][0]
        mn = data["temperature_2m_min"][0]
        return round((mx + mn) / 2, 1)
    except Exception:
        pass
    return round(35.0 - (abs(lat) - 25) * 0.7, 1)


# ==========================================
# 6. 双引擎数据源之二：NWS (美国国家气象局官方高精 7 日预报通道)
# ==========================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_nws_raw_data(lat, lon):
    headers = {
        "User-Agent": "(MyClimateAnalysisSystem, contact@myclimateapp.com)"
    }
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    res_points = requests.get(points_url, headers=headers, timeout=5.0)
    if res_points.status_code != 200:
        raise RuntimeWarning("NWS grid points matching failed")
    
    forecast_url = res_points.json()["properties"]["forecast"]
    
    res_forecast = requests.get(forecast_url, headers=headers, timeout=5.0)
    if res_forecast.status_code == 200:
        return res_forecast.json()["properties"]["periods"]
    raise RuntimeWarning("NWS forecast parsing failed")


def get_nws_forecast(lat, lon):
    try:
        periods = fetch_nws_raw_data(lat, lon)
        
        daily_aggregation = defaultdict(list)
        for period in periods:
            date_str = period["startTime"][:10]  
            
            temp_f = period["temperature"]
            temp_c = (temp_f - 32) * 5.0 / 9.0 if period.get("temperatureUnit") == "F" else temp_f
            
            pop = period.get("probabilityOfPrecipitation", {}).get("value") or 0
            short_forecast = period.get("shortForecast", "Unknown")
            
            daily_aggregation[date_str].append({
                "temp": temp_c,
                "pop": pop,
                "short_forecast": short_forecast
            })
            
        dates = sorted(list(daily_aggregation.keys()))[:7]
        max_temps = []
        min_temps = []
        precips = []
        forecasts_text = []
        
        for d in dates:
            day_records = daily_aggregation[d]
            temps = [r["temp"] for r in day_records]
            pops = [r["pop"] for r in day_records]
            txts = [r["short_forecast"] for r in day_records]
            
            max_temps.append(max(temps))
            min_temps.append(min(temps))
            precips.append(max(pops))
            forecasts_text.append(txts[0])
            
        return {
            "time": dates,
            "temperature_2m_max": max_temps,
            "temperature_2m_min": min_temps,
            "precipitation_probability": precips,
            "forecast_text": forecasts_text,
            "is_simulated": False,
            "data_source": "NWS (US Government Official)"
        }
    except Exception:
        sim = generate_geographical_weather(lat, lon)
        sim["forecast_text"] = ["多云" for _ in range(14)]
        return sim


def get_nws_emoji(text):
    text_lower = text.lower()
    if "sunny" in text_lower or "clear" in text_lower:
        return "☀️"
    elif "mostly sunny" in text_lower or "partly cloudy" in text_lower or "partly sunny" in text_lower:
        return "🌤️"
    elif "mostly cloudy" in text_lower:
        return "⛅"
    elif "cloudy" in text_lower or "overcast" in text_lower:
        return "☁️"
    elif "fog" in text_lower or "mist" in text_lower:
        return "🌫️"
    elif "drizzle" in text_lower or "sprinkle" in text_lower:
        return "🌧️"
    elif "rain" in text_lower or "shower" in text_lower:
        return "🌧️"
    elif "snow" in text_lower or "sleet" in text_lower or "ice" in text_lower or "flurry" in text_lower:
        return "❄️"
    elif "thunderstorm" in text_lower or "tstorm" in text_lower:
        return "⛈️"
    return "⛅"


# ==========================================
# 7. 级联气象过滤中心
# ==========================================
st.markdown("##### 🔍 气象过滤中心")
filter_cols = st.columns(3)

if "active_panel" not in st.session_state:
    st.session_state.active_panel = "天气预报"

cold_states_list = []
warm_states_list = []
for state, coords in US_CAPITALS.items():
    t_check = quick_check_temp(coords["lat"], coords["lon"])
    if t_check < temp_threshold:
        cold_states_list.append(state)
    else:
        warm_states_list.append(state)

with filter_cols[0]:
    selected_zone_filter = st.selectbox(
        "1. 冷暖类型筛选 (Climate Zone)", 
        options=["全部 (All States)", "冷区 (Cold Zone)", "暖区 (Warm Zone)"],
        key="zone_filter_selectbox"
    )

# 动态 CSS：根据冷暖区选择，自动使右侧 multiselect 标签变蓝/红
if "冷区" in selected_zone_filter:
    st.markdown("""
    <style>
        div[data-baseweb="tag"], span[data-baseweb="tag"] {
            background-color: #2563EB !important; /* 经典深蓝色 */
            color: #FFFFFF !important;
        }
        div[data-baseweb="tag"] span, span[data-baseweb="tag"] span {
            color: #FFFFFF !important;
        }
        div[data-baseweb="tag"] svg, span[data-baseweb="tag"] svg {
            fill: #FFFFFF !important;
        }
    </style>
    """, unsafe_allow_html=True)
elif "暖区" in selected_zone_filter:
    st.markdown("""
    <style>
        div[data-baseweb="tag"], span[data-baseweb="tag"] {
            background-color: #EF4444 !important; /* 珊瑚红 */
            color: #FFFFFF !important;
        }
        div[data-baseweb="tag"] span, span[data-baseweb="tag"] span {
            color: #FFFFFF !important;
        }
        div[data-baseweb="tag"] svg, span[data-baseweb="tag"] svg {
            fill: #FFFFFF !important;
        }
    </style>
    """, unsafe_allow_html=True)

if "冷区" in selected_zone_filter:
    states_options = sorted(cold_states_list)
elif "暖区" in selected_zone_filter:
    states_options = sorted(warm_states_list)
else:
    states_options = sorted(list(US_CAPITALS.keys()))

# ==========================================
# 联动机制重构：确保 Forecast 与 Trends 状态安全同步
# ==========================================
if st.session_state.active_panel == "天气预报":
    # 规则 3：如果趋势页面多选了城市，切换到天气预报页面就恢复默认城市
    if len(st.session_state.current_selected_states) > 1:
        default_city = "Alabama (Montgomery)" if "Alabama (Montgomery)" in states_options else states_options[0]
        st.session_state.current_selected_states = [default_city]
        
    current_single_state = st.session_state.current_selected_states[0]
    if current_single_state not in states_options:
        current_single_state = states_options[0]
        st.session_state.current_selected_states = [current_single_state]
        
    with filter_cols[1]:
        selected_state = st.selectbox(
            "2. 选择代表州 (State)", 
            options=states_options,
            index=states_options.index(current_single_state),
            key="state_single_widget"
        )
        st.session_state.current_selected_states = [selected_state]
    selected_states = [selected_state]
else:
    # 趋势多选页面逻辑
    valid_stored_states = [s for s in st.session_state.current_selected_states if s in states_options]
    if not valid_stored_states:
        valid_stored_states = [states_options[0]]
        st.session_state.current_selected_states = valid_stored_states
        
    with filter_cols[1]:
        selected_states = st.multiselect(
            "2. 选择代表州 (State) - 可多选",
            options=states_options,
            default=valid_stored_states,
            key="state_multi_widget"
        )
        if not selected_states:
            st.warning("请至少选择一个代表州加载趋势图。")
            st.stop()
        st.session_state.current_selected_states = selected_states

# 安全划分单州/多州数据提取
if len(selected_states) == 1:
    state_lat = US_CAPITALS[selected_states[0]]["lat"]
    state_lon = US_CAPITALS[selected_states[0]]["lon"]
    
    if st.session_state.active_panel == "天气预报":
        active_weather_main = get_nws_forecast(state_lat, state_lon)
    else:

    forecast_span_current = st.session_state.get(
        "span_selector",
        "未来14天 (Next 14 Days)"
    )

    if "未来7天" in forecast_span_current:
        active_weather_main = get_nws_forecast(state_lat, state_lon)
    else:
        active_weather_main = get_unified_weather(state_lat, state_lon)
        
    state_calc_temp = round(np.mean([active_weather_main["temperature_2m_max"][0], active_weather_main["temperature_2m_min"][0]]), 1)
    state_zone = "冷区 (Cold)" if state_calc_temp < temp_threshold else "暖区 (Warm)"
    zone_emoji = "❄️" if "冷" in state_zone else "☀️"
    
    with filter_cols[2]:
        st.metric(
            label="3. 当前代表州状态 (Status)", 
            value=f"{zone_emoji} {state_zone}", 
            delta=f"今日均温: {state_calc_temp}°C"
        )
    
    source_label = active_weather_main.get("data_source", "Unknown")
    is_simulated = active_weather_main.get("is_simulated", False)
else:
    temps = []
    simulated_flags = []
    for s in selected_states:
        s_lat, s_lon = US_CAPITALS[s]["lat"], US_CAPITALS[s]["lon"]
        s_data = get_unified_weather(s_lat, s_lon)
        t = round(np.mean([s_data["temperature_2m_max"][0], s_data["temperature_2m_min"][0]]), 1)
        temps.append(t)
        simulated_flags.append(s_data.get("is_simulated", False))
    
    avg_temp = round(np.mean(temps), 1)
    avg_zone = "冷区 (Cold)" if avg_temp < temp_threshold else "暖区 (Warm)"
    zone_emoji = "❄️" if "冷" in avg_zone else "☀️"
    
    with filter_cols[2]:
        st.metric(
            label="3. 组合分析状态 (Combined)",
            value=f"已选 {len(selected_states)} 个地区",
            delta=f"组合平均温度: {avg_temp}°C"
        )
    
    source_label = "Open-Meteo API"
    is_simulated = any(simulated_flags)

# 指示信息提示
if is_simulated:
    st.warning(f"⚠️ 提示：连接超时，部分或全部选定地区已自动降级至本地地理仿真引擎。")
else:
    st.success(f"✅ 双通道连接正常：成功通过 [{source_label}] 载入当前气象预测数据。")

st.write("---")

# ==========================================
# 8. 双导航控制大按钮 (Tab Switcher)
# ==========================================
col_btn_left, col_btn_right = st.columns(2)
with col_btn_left:
    if st.button("📅 天气预报", key="btn_panel_forecast", use_container_width=True):
        st.session_state.active_panel = "天气预报"
        st.rerun()

with col_btn_right:
    if st.button("📈 天气趋势", key="btn_panel_trends", use_container_width=True):
        st.session_state.active_panel = "天气趋势"
        st.rerun()

st.write("")


# ==========================================
# 9. 面板 A 渲染：天气预报 (NWS高精准7天引擎)
# ==========================================
if st.session_state.active_panel == "天气预报":
    target_state = selected_states[0]
    st.subheader(f"📅 {target_state} • 7日高精预报 (基于NWS)")
    
    cols_grid = st.columns(2)
    
    def get_weather_desc_and_emoji(index, raw_data):
        if "forecast_text" in raw_data:
            txt = raw_data["forecast_text"][index]
            return txt, get_nws_emoji(txt)
        else:
            mapping = {
                0: ("晴朗", "☀️"), 1: ("晴间多云", "🌤️"), 2: ("多云", "⛅"), 3: ("阴天", "☁️"), 
                61: ("小雨", "🌧️")
            }
            code = raw_data["weather_code"][index]
            return mapping.get(code, ("多云", "⛅"))

    display_days = min(7, len(active_weather_main["time"]))
    for i in range(display_days):
        col_idx = i % 2
        date_str = active_weather_main["time"][i]
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        day_label = date_obj.strftime("%A")
        day_label_zh = {
            "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三", "Thursday": "周四",
            "Friday": "周五", "Saturday": "周六", "Sunday": "周日"
        }.get(day_label, day_label)
        
        if i == 0: day_label_zh = "今天"
            
        cond_text, cond_emoji = get_weather_desc_and_emoji(i, active_weather_main)
        temp_max = active_weather_main["temperature_2m_max"][i]
        temp_min = active_weather_main["temperature_2m_min"][i]
        precip = active_weather_main["precipitation_probability"][i]
        
        disp_max = int(round(temp_max))
        disp_min = int(round(temp_min))
        disp_diff = disp_max - disp_min

        card_class = "weather-card weather-card-today" if i == 0 else "weather-card"
        
        card_html = f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 800; color: #1E293B; font-size: 16px;">
                    {day_label_zh} <span style="font-size: 12px; color: #64748B; font-weight: 400;">{date_str[5:].replace('-', '/')}</span>
                </span>
                <span style="font-size: 14px; font-weight: 700; color: #475569;">{cond_text}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                <span style="font-size: 58px; line-height: 1;">{cond_emoji}</span>
                <div style="font-size: 13px; color: #475569; text-align: right; line-height: 1.5; font-weight: 500;">
                    🌧️ 降水概率: {precip}%
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 14px;">
                <span style="font-size: 28px; font-weight: 800; color: #0F172A; line-height: 1;">{disp_min}° - {disp_max}°</span>
                <span style="font-size: 12px; color: #94A3B8; font-weight: 600;">温差: {disp_diff}°C</span>
            </div>
        </div>
        """
        with cols_grid[col_idx]:
            st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# 10. 面板 B 渲染：天气趋势
# ==========================================
elif st.session_state.active_panel == "天气趋势":

    num_selected = len(selected_states)

    # 预测跨度选择
    forecast_span = st.selectbox(
        "选择预测跨度 (Forecast Range):",
        options=[
            "未来7天 (Next 7 Days)",
            "未来14天 (Next 14 Days)",
            "未来5周 (Next 5 Weeks)"
        ],
        key="span_selector"
    )

    # 动态标题与数据源
    trend_source = "NWS" if "未来7天" in forecast_span else "Open-Meteo"

    if num_selected == 1:
        st.subheader(f"📈 {selected_states[0]} • 中期趋势 (基于{trend_source})")
    else:
        st.subheader(f"📈 美国多区气候 • 中期趋势 (基于{trend_source})")

    # ==========================================
    # 动态加载数据源
    # ==========================================
    states_weather_data = {}

    for s in selected_states:

        s_lat = US_CAPITALS[s]["lat"]
        s_lon = US_CAPITALS[s]["lon"]

        # 未来7天 -> 使用 NWS
        if "未来7天" in forecast_span:
            states_weather_data[s] = get_nws_forecast(s_lat, s_lon)

        # 未来14天 / 未来5周 -> 使用 Open-Meteo
        else:
            states_weather_data[s] = get_unified_weather(s_lat, s_lon)

    # ==========================================
    # 数据处理
    # ==========================================

    if "未来7天" in forecast_span:

        available_days = min(
        7,
            len(states_weather_data[selected_states[0]]["time"])
    )

        x_timeline = [
            states_weather_data[selected_states[0]]["time"][i]
            for i in range(available_days)
    ]

        y_data_per_state = {}

        for s in selected_states:
            y_data_per_state[s] = [
                round(
                    (
                        states_weather_data[s]["temperature_2m_max"][i]
                        + states_weather_data[s]["temperature_2m_min"][i]
                    ) / 2,
                    1
                )
                for i in range(available_days)
            ]

        y_axis_title = "日平均气温 (°C)"

    elif "未来14天" in forecast_span:

        x_timeline = [
            states_weather_data[selected_states[0]]["time"][i]
            for i in range(14)
        ]

        y_data_per_state = {}

        for s in selected_states:
            y_data_per_state[s] = [
                round(
                    (
                        states_weather_data[s]["temperature_2m_max"][i]
                        + states_weather_data[s]["temperature_2m_min"][i]
                    ) / 2,
                    1
                )
                for i in range(14)
            ]

        y_axis_title = "日平均气温 (°C)"

    else:

        x_timeline = [
            "Week 1",
            "Week 2",
            "Week 3",
            "Week 4",
            "Week 5"
        ]

        y_data_per_state = {}

        for s in selected_states:
            y_data_per_state[s] = states_weather_data[s]["weeks_trend"]

        y_axis_title = "周平均气温 (°C)"


    points_count = len(x_timeline)
    averaged_trend = []
    for i in range(points_count):
        points_sum = [y_data_per_state[s][i] for s in selected_states]
        averaged_trend.append(round(np.mean(points_sum), 1))

    # ==========================================
    # 趋势折线图绘制与坐标轴范围配置
    # ==========================================
    fig = go.Figure()
    
    # 保证只有一个城市时，不重复绘制单独城市的实线
    if 1 < num_selected <= 15:
        for s in selected_states:
            fig.add_trace(go.Scatter(
                x=x_timeline, 
                y=y_data_per_state[s],
                mode='lines+markers',                 
                name=f"{s} 趋势",
                line=dict(width=2),                  
                marker=dict(size=6, symbol='circle'), 
                hoverinfo='all'                       
            ))

    # 确定平均线颜色
    if "冷区" in selected_zone_filter:
        main_color = '#3B82F6' 
    elif "暖区" in selected_zone_filter:
        main_color = '#EF4444' 
    else:
        main_color = '#EF4444' if np.mean(averaged_trend) >= temp_threshold else '#3B82F6'

    # 绘制平均趋势主虚线
    # 动态调整主线的 name 图例名称：单城市显示其城市名趋势，多城市显示“所选组合均值”
    fig.add_trace(go.Scatter(
        x=x_timeline, y=averaged_trend,
        mode='lines+markers+text',
        name=f"{selected_states[0]} 趋势" if num_selected == 1 else "所选组合均值",
        line=dict(color=main_color, width=4, dash='dash', shape='spline'),
        marker=dict(size=9, symbol='circle', line=dict(color='#FFFFFF', width=1.5)),
        text=[f"<b>{v}°</b>" for v in averaged_trend], 
        textposition="top center",
        textfont=dict(size=11, color="#0F172A")
    ))

    # 判定阈值线
    fig.add_hline(
        y=temp_threshold, 
        line_width=1.5, 
        line_dash="dot", 
        line_color="#64748B",
        annotation_text=f"判定阈值 {temp_threshold}°C",
        annotation_position="bottom right"
    )

    fig.update_layout(
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#F1F5F9'),
        yaxis=dict(
            title=y_axis_title, 
            showgrid=True, 
            gridcolor='#F1F5F9', 
            ticksuffix="°C", 
            range=[10, 45]  
        ),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=20, b=40),
        height=800
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 智能气候分析结论卡
    # ==========================================
    st.write("---")
    
    trend_symbol = "↗ 逐步上升" if averaged_trend[-1] > averaged_trend[0] else ("↘ 逐步下降" if averaged_trend[-1] < averaged_trend[0] else "→ 基本平稳")
    is_cold = np.mean(averaged_trend) < temp_threshold
    rec_tags = "秋装服饰 / 防风外套 / 针织衫 / 卫衣" if is_cold else "夏季服饰 / 轻薄T恤 / 户外用品 / 防晒产品"
    
    analysis_html = f"""
    <div class="analysis-card">
        <h3 style="margin: 0 0 15px 0; color: #1E293B; font-size: 18px;">📊 气候分析结论 (基于所选地区 average 趋势)</h3>
        <div style="line-height: 1.8; font-size: 14px; color: #475569;">
            <p><strong>预测期内平均气温：</strong> 预计为 <strong>{round(np.mean(averaged_trend), 1)}°C</strong></p>
            <p><strong>所选跨度温度走势：</strong> <span style="font-weight: bold; color: {'#EF4444' if '上升' in trend_symbol else '#3B82F6'};">{trend_symbol}</span></p>
            <p><strong>综合气候分类评定：</strong> <span style="font-weight: bold; color: {'#3B82F6' if is_cold else '#F97316'};">{"冷区 (Cold Zone)" if is_cold else "暖区 (Warm Zone)"}</span></p>
            <p><strong>供应链/陈列推荐关注：</strong> <span style="font-weight: bold; color: #0F766E;">{rec_tags}</span></p>
        </div>
    </div>
    """
    st.markdown(analysis_html, unsafe_allow_html=True)
