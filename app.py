import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Business Dashboard", page_icon="🏪", layout="wide")

TOTAL_REGION = "รวม"                    # แถวผลรวมทั้งประเทศ
TOTAL_ACTIVITY = "จำนวนสถานประกอบการ"   # แถวผลรวมทุกกิจกรรม


# ---------- โหลดและทำความสะอาดข้อมูล ----------
@st.cache_data
def load_data(path="data.csv"):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    for c in ["region", "eco_activity", "unit", "source"]:
        df[c] = df[c].astype(str).str.strip()
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error("ไม่พบไฟล์ data.csv กรุณาวางไว้โฟลเดอร์เดียวกับ app.py")
    st.stop()

# แยกแถวผลรวมออก เพื่อไม่ให้นับซ้ำ
regions_df = df[df["region"] != TOTAL_REGION]
totals_by_region = regions_df[regions_df["eco_activity"] == TOTAL_ACTIVITY]
activity_df = regions_df[regions_df["eco_activity"] != TOTAL_ACTIVITY]

# ---------- ส่วนหัว ----------
st.title("🏪 Business Establishment Dashboard")
st.markdown("**Dashboard จำนวนสถานประกอบการของประเทศไทย**")
st.write("ใช้วิเคราะห์จำนวนสถานประกอบการแยกตามภาคและประเภทกิจกรรมทางเศรษฐกิจ "
         "ข้อมูลจากสำนักงานสถิติแห่งชาติ ผ่าน data.go.th")

# ---------- Interactive Widgets ----------
st.sidebar.header("🔎 Filter ข้อมูล")
years = sorted(df["year"].unique())
year = st.sidebar.selectbox("ปี (พ.ศ.)", years, index=len(years) - 1)

all_regions = totals_by_region["region"].unique().tolist()
sel_regions = st.sidebar.multiselect("ภาค", all_regions, default=all_regions)

all_acts = activity_df["eco_activity"].unique().tolist()
sel_acts = st.sidebar.multiselect("ประเภทกิจกรรม", all_acts, default=all_acts)

top_n = st.sidebar.slider("จำนวนกิจกรรมที่แสดงในกราฟอันดับ", 3, len(all_acts), 10)

if not sel_regions or not sel_acts:
    st.warning("กรุณาเลือกอย่างน้อย 1 ภาค และ 1 ประเภทกิจกรรม")
    st.stop()

f_tot = totals_by_region[(totals_by_region["year"] == year) &
                         (totals_by_region["region"].isin(sel_regions))]
f_act = activity_df[(activity_df["year"] == year) &
                    (activity_df["region"].isin(sel_regions)) &
                    (activity_df["eco_activity"].isin(sel_acts))]

# ---------- สรุปข้อมูล ----------
st.header("📊 สรุปข้อมูล")
by_act = f_act.groupby("eco_activity")["value"].sum().sort_values(ascending=False)
top_region = f_tot.loc[f_tot["value"].idxmax()] if len(f_tot) else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("สถานประกอบการทั้งหมด", f"{f_tot['value'].sum():,.0f} แห่ง")
c2.metric("ภาคที่มีมากที่สุด", top_region["region"] if top_region is not None else "-")
c3.metric("กิจกรรมที่มีมากที่สุด", by_act.index[0] if len(by_act) else "-")
c4.metric("จำนวนภาคที่เลือก", f"{len(sel_regions)} ภาค")
st.divider()

# ---------- กราฟ 1: จำนวนสถานประกอบการตามภาค ----------
st.header("🗺️ จำนวนสถานประกอบการตามภาค")
g1 = f_tot.sort_values("value", ascending=False)
fig1 = px.bar(g1, x="region", y="value", text_auto=",.0f",
              labels={"region": "ภาค", "value": "จำนวน (แห่ง)"},
              color_discrete_sequence=["#5DADE2"])
st.plotly_chart(fig1, width="stretch")

# ---------- กราฟ 2: อันดับประเภทกิจกรรม + สัดส่วนตามภาค ----------
left, right = st.columns(2)
with left:
    st.subheader(f"🏆 {top_n} ประเภทกิจกรรมที่มีสถานประกอบการมากที่สุด")
    g2 = by_act.head(top_n).reset_index().sort_values("value")
    fig2 = px.bar(g2, x="value", y="eco_activity", orientation="h",
                  labels={"eco_activity": "", "value": "จำนวน (แห่ง)"},
                  color_discrete_sequence=["#5DADE2"])
    st.plotly_chart(fig2, width="stretch")
with right:
    st.subheader("🥧 สัดส่วนสถานประกอบการตามภาค")
    fig3 = px.pie(g1, names="region", values="value", hole=0.45)
    st.plotly_chart(fig3, width="stretch")

# ---------- กราฟ 3: เทียบกิจกรรมแต่ละภาค ----------
st.header("📈 เปรียบเทียบประเภทกิจกรรมในแต่ละภาค")
fig4 = px.bar(f_act, x="region", y="value", color="eco_activity",
              labels={"region": "ภาค", "value": "จำนวน (แห่ง)", "eco_activity": "ประเภทกิจกรรม"})
st.plotly_chart(fig4, width="stretch")

# ---------- ตาราง + ดาวน์โหลด ----------
st.header("📋 รายละเอียดข้อมูล")
show = f_act.rename(columns={"year": "ปี", "region": "ภาค", "eco_activity": "ประเภทกิจกรรม",
                             "value": "จำนวน", "unit": "หน่วย", "source": "แหล่งข้อมูล"})
st.dataframe(show, width="stretch", hide_index=True)

st.header("⬇️ Download")
st.download_button("ดาวน์โหลดข้อมูลที่กรองแล้ว (CSV)",
                   show.to_csv(index=False).encode("utf-8-sig"),
                   "filtered_data.csv", "text/csv")
