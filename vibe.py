import streamlit as st
import datetime
from lunar_python import Solar
import google.generativeai as genai # 引入 AI 大脑

# ================= 网页基础设定 =================
st.set_page_config(page_title="亭云子奇门大师", layout="centered")

# ================= AI 密钥初始化 =================
# 尝试从 Streamlit Secrets 中读取您刚存好的 API Key
api_ready = False
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        api_ready = True
except Exception:
    pass

# ================= 状态管理：时间锚点 =================
bj_tz = datetime.timezone(datetime.timedelta(hours=8))
if 'target_dt' not in st.session_state:
    st.session_state.target_dt = datetime.datetime.now(bj_tz)

now = st.session_state.target_dt

# ================= 1. 核心配置 =================
QM_RULES = {
    "冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6], "立春": [8, 5, 2],
    "雨水": [9, 6, 3], "惊蛰": [1, 7, 4], "春分": [3, 9, 6], "清明": [4, 1, 7],
    "谷雨": [5, 2, 8], "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9],
    "夏至": [13, 19, 16], "小暑": [14, 20, 17], "大暑": [15, 21, 18], "立秋": [20, 17, 14],
    "处暑": [19, 16, 13], "白露": [13, 19, 16], "秋分": [15, 21, 18], "寒露": [18, 15, 12],
    "霜降": [17, 14, 11], "立冬": [18, 15, 12], "小雪": [17, 14, 11], "大雪": [16, 22, 19]
}
STEM_ORDER = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
YANG_STEMS = ["甲", "丙", "戊", "庚", "壬"] 
GATES_HOME = {1:"休", 2:"死", 3:"伤", 4:"杜", 6:"开", 7:"惊", 8:"生", 9:"景"}
STARS_HOME = {1:"蓬", 2:"芮", 3:"冲", 4:"辅", 6:"心", 7:"柱", 8:"任", 9:"英"}

GATES_ORDER = ["休", "生", "伤", "杜", "景", "死", "惊", "开"] 
STARS_ORDER = ["蓬", "任", "冲", "辅", "英", "芮", "柱", "心"]
PATH = [1, 8, 3, 4, 9, 2, 7, 6] 
GODS = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
XUN_SHOU_LIUYI = {"甲子":"戊", "甲戌":"己", "甲申":"庚", "甲午":"辛", "甲辰":"壬", "甲寅":"癸"}

# ================= 2. 历法与子时跨日引擎 =================
calc_time = now
if now.hour >= 23:
    calc_time = now + datetime.timedelta(hours=1)

lunar = Solar.fromYmdHms(calc_time.year, calc_time.month, calc_time.day, calc_time.hour, calc_time.minute, calc_time.second).getLunar()
day_p, hour_p = lunar.getDayInGanZhi(), lunar.getTimeInGanZhi()
jie_qi = lunar.getPrevJieQi(True).getName()
month_zhi = lunar.getMonthInGanZhi()[1]

# ================= 3. 真·符头地支定三元 =================
jia_zi = [["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"][i%10]+["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"][i%12] for i in range(60)]
fu_tou = jia_zi[jia_zi.index(day_p) - (jia_zi.index(day_p) % 5)]

ft_zhi = fu_tou[1]
if ft_zhi in ["子", "午", "卯", "酉"]:
    yuan = "上"
elif ft_zhi in ["寅", "申", "巳", "亥"]:
    yuan = "中"
else:
    yuan = "下"

raw_ju = QM_RULES[jie_qi][{"上":0, "中":1, "下":2}[yuan]]
is_yang = raw_ju <= 12
ju_num = raw_ju if is_yang else raw_ju - 12

# ================= 4. 排地盘 =================
dipan = {}
for i, s in enumerate(STEM_ORDER):
    p = (ju_num + i - 1) % 9 + 1 if is_yang else (ju_num - i - 1) % 9 + 1
    if p <= 0: p += 9
    dipan[p] = s

# ================= 5. 排三盘 =================
hour_idx = jia_zi.index(hour_p)
xun_shou = jia_zi[hour_idx - (hour_idx % 10)]
shou_liuyi = XUN_SHOU_LIUYI[xun_shou]

hour_stem = hour_p[0]
target_stem = shou_liuyi if hour_stem == "甲" else hour_stem
zhifu_palace = [p for p, s in dipan.items() if s == target_stem][0]

shou_init_p = [p for p, s in dipan.items() if s == shou_liuyi][0]
z_shi_gate = GATES_HOME[shou_init_p if shou_init_p != 5 else 2] 
z_shi_star = STARS_HOME[shou_init_p if shou_init_p != 5 else 2] 

bashen, bamen, jiuxing, tianpan = {i: "　　" for i in range(1, 10)}, {i: "　" for i in range(1, 10)}, {i: "　" for i in range(1, 10)}, {i: "" for i in range(1, 10)}

if zhifu_palace in PATH:
    start_idx = PATH.index(zhifu_palace)
    star_start_idx = STARS_ORDER.index(z_shi_star)
    for i in range(8):
        p_idx = (start_idx + i) % 8 if is_yang else (start_idx - i) % 8
        bashen[PATH[p_idx]] = GODS[i]
        target_p = PATH[(start_idx + i) % 8]
        current_star = STARS_ORDER[(star_start_idx + i) % 8]
        jiuxing[target_p] = current_star
        original_p = PATH[(star_start_idx + i) % 8]
        tianpan[target_p] = (dipan[original_p] + dipan[5]) if current_star == "芮" else dipan[original_p]

steps = hour_idx % 10
zhishi_palace = (shou_init_p + steps - 1) % 9 + 1 if is_yang else (shou_init_p - steps - 1) % 9 + 1
if zhishi_palace <= 0: zhishi_palace += 9
if zhishi_palace == 5: zhishi_palace = 2

if zhishi_palace in PATH:
    gate_start_idx = GATES_ORDER.index(z_shi_gate)
    path_start_idx = PATH.index(zhishi_palace)
    for i in range(8):
        bamen[PATH[(path_start_idx + i) % 8]] = GATES_ORDER[(gate_start_idx + i) % 8]

# ================= 6. 神煞推演 =================
hour_zhi = hour_p[1]
MA_XING_MAP = {"申": 8, "子": 8, "辰": 8, "亥": 4, "卯": 4, "未": 4, "寅": 2, "午": 2, "戌": 2, "巳": 6, "酉": 6, "丑": 6}
ma_xing_p = MA_XING_MAP[hour_zhi]
KONG_WANG_MAP = {"甲子":["戌","亥"], "甲戌":["申","酉"], "甲申":["午","未"], "甲午":["辰","巳"], "甲辰":["寅","卯"], "甲寅":["子","丑"]}
ZHI_TO_P = {"子":1, "丑":8, "寅":8, "卯":3, "辰":4, "巳":4, "午":9, "未":2, "申":2, "酉":7, "戌":6, "亥":6}
kw_zhi_list = KONG_WANG_MAP[xun_shou]
kw_palaces = [ZHI_TO_P[z] for z in kw_zhi_list]

# ================= 7. 能量学说引擎 =================
P_WX = {1:"水", 2:"土", 3:"木", 4:"木", 5:"土", 6:"金", 7:"金", 8:"土", 9:"火"}
STAR_WX = {"蓬":"水","任":"土","冲":"木","辅":"木","英":"火","芮":"土","柱":"金","心":"金","禽":"土"}
GATE_WX = {"休":"水","生":"土","伤":"木","杜":"木","景":"火","死":"土","惊":"金","开":"金"}
WX_MAP = {"木":0, "火":1, "土":2, "金":3, "水":4}

def get_star_state(star, p):
    if not star or star == "　": return "　"
    s = WX_MAP[STAR_WX[star]]
    p_elem = WX_MAP[P_WX[p]]
    if s == p_elem: return "相"
    if (s + 1) % 5 == p_elem: return "旺"
    if (p_elem + 1) % 5 == s: return "废"
    if (s + 2) % 5 == p_elem: return "休"
    return "囚"

def get_gate_state(gate, p):
    if not gate or gate == "　": return "　"
    g = WX_MAP[GATE_WX[gate]]
    p_elem = WX_MAP[P_WX[p]]
    if g == p_elem: return "旺"
    if (p_elem + 1) % 5 == g: return "相"
    if (g + 1) % 5 == p_elem: return "休"
    if (g + 2) % 5 == p_elem: return "迫"
    return "制"

CS_NAMES = ["生","沐","冠","临","旺","衰","病","死","墓","绝","胎","养"]
CS_START = {"甲":11, "乙":6, "丙":2, "丁":9, "戊":2, "己":9, "庚":5, "辛":0, "壬":8, "癸":3}
CS_DIR = {"甲":1, "乙":-1, "丙":1, "丁":-1, "戊":1, "己":-1, "庚":1, "辛":-1, "壬":1, "癸":-1}
P_ZHI = {1:[0], 8:[1,2], 3:[3], 4:[4,5], 9:[6], 2:[7,8], 7:[9], 6:[10,11], 5:[7,8]} 

def get_cs(stem_str, p, explicit_host=None):
    if not stem_str or stem_str.replace("　", "") == "": return "　　"
    stem_str = stem_str.replace("　", "")
    host = explicit_host if explicit_host else stem_str[0]
    if host not in CS_START: return "　　"
    zhis = P_ZHI.get(p, [])
    if not zhis: return "　　"
    if len(zhis) == 1:
        target_zhi = zhis[0]
    else:
        is_yang = host in YANG_STEMS
        target_zhi = zhis[0] 
        for z in zhis:
            if (z % 2 == 0) == is_yang:
                target_zhi = z
                break
    res = ""
    for s in stem_str:
        if s not in CS_START: continue
        idx = (target_zhi - CS_START[s]) * CS_DIR[s] % 12
        res += CS_NAMES[idx]
    if len(res) == 1: return "　" + res 
    if len(res) == 0: return "　　"
    return res[:2]

STEM_TO_ZHI = {"戊":"子", "己":"戌", "庚":"申", "辛":"午", "壬":"辰", "癸":"寅"}
P_ZHI_CHARS = {1:["子"], 8:["丑","寅"], 3:["卯"], 4:["辰","巳"], 9:["午"], 2:["未","申"], 7:["酉"], 6:["戌","亥"], 5:["未","申"]}

def get_stem_relation(stem_str, p):
    if not stem_str or stem_str.replace("　", "") == "": return "　"
    s = stem_str.replace("　", "")[0] 
    if s not in STEM_TO_ZHI: return "　"
    z1 = STEM_TO_ZHI[s]
    
    p_zhis = P_ZHI_CHARS.get(p, [])
    matched = "　"
    priority = {"刑": 4, "冲": 3, "合": 2, "害": 1, "　": 0}
    
    for z2 in p_zhis:
        xing_sets = [{"子","卯"}, {"寅","巳"}, {"巳","申"}, {"申","寅"}, {"丑","戌"}, {"戌","未"}, {"未","丑"}]
        if {z1, z2} in xing_sets or (z1 == z2 and z1 in ["辰","午","酉","亥"]):
            if priority["刑"] > priority[matched]: matched = "刑"
        chong_pairs = [{"子","午"}, {"丑","未"}, {"寅","申"}, {"卯","酉"}, {"辰","戌"}, {"巳","亥"}]
        if {z1, z2} in chong_pairs:
            if priority["冲"] > priority[matched]: matched = "冲"
        he_pairs = [{"子","丑"}, {"寅","亥"}, {"卯","戌"}, {"辰","酉"}, {"巳","申"}, {"午","未"}]
        if {z1, z2} in he_pairs:
            if priority["合"] > priority[matched]: matched = "合"
        hai_pairs = [{"子","未"}, {"丑","午"}, {"寅","巳"}, {"卯","辰"}, {"申","亥"}, {"酉","戌"}]
        if {z1, z2} in hai_pairs:
            if priority["害"] > priority[matched]: matched = "害"
            
    return matched

# ================= 8. HTML 渲染引擎 =================
RED = "<span style='color: #FF4B4B; font-weight: bold;'>"
CYAN = "<span style='color: #00E5FF;'>"
PURPLE = "<span style='color: #B185FF;'>"
BROWN = "<span style='color: #D48A4C;'>"
GRAY = "<span style='color: #808495;'>"
RESET = "</span>"

prefix = "阳" if is_yang else "阴"
html_output = f"<div style='font-family: monospace, \"Microsoft YaHei\"; font-size: 16px; background-color: #1E1E1E; color: #FFFFFF; padding: 20px; border-radius: 10px; line-height: 1.5; white-space: pre; overflow-x: auto;'>"
html_output += f"{'='*56}\n"
html_output += f" ☯️ 奇门遁甲全息排盘: {jie_qi} · {prefix}遁 {ju_num} 局 ☯️\n"
html_output += f" 四柱: {lunar.getYearInGanZhi()}年 {lunar.getMonthInGanZhi()}月 {day_p}日 {hour_p}时\n"
html_output += f" 大将: 值符[{RED}{z_shi_star}{RESET}]落{zhifu_palace}宫，先锋: 值使[{RED}{z_shi_gate}{RESET}]落{zhishi_palace}宫\n"
html_output += f"{'='*56}\n"

def get_p_lines(p):
    if p == 5:
        d = dipan.get(5, "")
        if d:
            d_pad = "　" + d if len(d) == 1 else d
            return [
                "　　　　　　",
                "　　　　　　",
                f"　　{d_pad}　　",
                "　　　　　　",
                "　　　　　　"
            ]
        else:
            return ["　　　　　　"] * 5
    
    g = bashen.get(p, "") or "　　"
    x = jiuxing.get(p, "") or "　"
    m = bamen.get(p, "") or "　"
    
    t = tianpan.get(p, "")
    t_pad = "　" + t if len(t) == 1 else (t if t else "　　")
    d = (dipan[p] + dipan[5]) if p == 2 else dipan.get(p, "")
    d_pad = "　" + d if len(d) == 1 else (d if d else "　　")
    
    x_state = get_star_state(x, p)
    m_state = get_gate_state(m, p)
    t_cs = get_cs(t, p)
    d_cs = get_cs(d, p)
    
    t_rel = get_stem_relation(t, p)
    d_rel = get_stem_relation(d, p)
    
    x_disp = f"{RED}{x}{RESET}" if x == z_shi_star else f"{PURPLE}{x}{RESET}"
    m_disp = f"{RED}{m}{RESET}" if m == z_shi_gate else f"{BROWN}{m}{RESET}"
    mk1 = f"{CYAN}马{RESET}" if p == ma_xing_p else "　"
    mk2 = f"{RED}空{RESET}" if p in kw_palaces else "　"
    
    xs_disp = f"{GRAY}{x_state}{RESET}" if x_state != "　" else "　"
    ms_disp = f"{GRAY}{m_state}{RESET}" if m_state != "　" else "　"
    t_rel_disp = f"{RED}{t_rel}{RESET}" if t_rel != "　" else "　"
    d_rel_disp = f"{RED}{d_rel}{RESET}" if d_rel != "　" else "　"
    
    l1 = f"{mk1}　{g}　{mk2}"       
    l2 = f"{x_disp}　　　{t_pad}"     
    l3 = f"{xs_disp}　　{t_rel_disp}{GRAY}{t_cs}{RESET}"   
    l4 = f"{m_disp}　　　{d_pad}"     
    l5 = f"{ms_disp}　　{d_rel_disp}{GRAY}{d_cs}{RESET}"   
    
    return [l1, l2, l3, l4, l5]

rows = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
for r_idx, row in enumerate(rows):
    lines = [get_p_lines(p) for p in row]
    for i in range(5):
        html_output += f" {lines[0][i]} │ {lines[1][i]} │ {lines[2][i]} \n"
    if r_idx < 2:
        html_output += " ──────────────┼──────────────┼────────────── \n"

html_output += "</div>"

# ================= 9. UI 布局呈现与 AI 交互 =================
st.markdown(html_output, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    # 使用多标签页，让页面保持整洁
    tab1, tab2 = st.tabs(["⏳ 时空穿梭", "🤖 亭云子考核"])
    
    with tab1:
        st.markdown("### 🗓️ 时空穿梭推演")
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("拨动选择年月日", now.date())
        with col2:
            new_time = st.time_input("拨动选择时分", now.time())
            
        if st.button("🚀 按选择时间重新排盘", type="primary", use_container_width=True):
            st.session_state.target_dt = datetime.datetime.combine(new_date, new_time).replace(tzinfo=bj_tz)
            st.rerun()

    with tab2:
        st.markdown("### 🧙‍♂️ 亭云子实战抽查")
        if not api_ready:
            st.warning("⚠️ 尚未连接到 AI 大脑。请确保您已在 Streamlit 的 Secrets 中配置了 `GEMINI_API_KEY`。")
        else:
            st.markdown("点击下方按钮，师傅将基于当前盘面为您出一道实战考题。")
            if st.button("⚡ 请师傅出题", type="primary", use_container_width=True):
                with st.spinner("亭云子正在闭目推演阵法，为您甄选考题..."):
                    
                    # 将盘面核心数据提纯为文本，传给 AI 大脑
                    ai_prompt = f"当前排盘时间：{lunar.getYearInGanZhi()}年 {lunar.getMonthInGanZhi()}月 {day_p}日 {hour_p}时\n"
                    ai_prompt += f"核心信息：{prefix}遁{ju_num}局，旬首{xun_shou}，值符{z_shi_star}落{zhifu_palace}宫，值使{z_shi_gate}落{zhishi_palace}宫。空亡在{''.join(kw_zhi_list)}。\n"
                    for p in range(1, 10):
                        ai_prompt += f"第{p}宫：神[{bashen.get(p,'')}] 星[{jiuxing.get(p,'')}] 门[{bamen.get(p,'')}] 天盘[{tianpan.get(p,'')}] 地盘[{dipan.get(p,'')}]\n"
                    
                    # 极其严格的 AI 人设与出题规则定制
                    system_instruction = """
                    你是“亭云子奇门大师”，一位极其严厉、注重实战逻辑的导师。
                    请根据用户提供的九宫格盘面状态，立刻找出一个值得考察的切入点（例如格局吉凶、星门旺衰、击刑空亡等）。
                    强制规则：为了方便用户使用手机快速答题，你提出的问题必须且只能是「单项选择题」或「判断题」。请直接输出干脆利落的题目和选项，绝不允许说多余的废话。
                    """
                    
                    try:
                        # 呼叫 Gemini 引擎
                        model = genai.GenerativeModel('gemini-1.5-pro', system_instruction=system_instruction)
                        response = model.generate_content(ai_prompt)
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"调用大师失败，请检查 API 密钥是否正确。错误信息：{e}")