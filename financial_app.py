#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة الإيرادات والمصروفات 2025
تطبيق شامل لقراءة وتحليل وإدارة البيانات المالية
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
from io import BytesIO

# =============================================================================
# إعدادات الصفحة
# =============================================================================
st.set_page_config(
    page_title="لوحة الإيرادات والمصروفات 2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS مخصص
# =============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
    }
    
    .main {
        padding: 2rem;
    }
    
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    h1, h2, h3 {
        color: #1e3c72;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# ثوابت الملفات
# =============================================================================
DATA_FILE = 'financial_data.json'
HISTORY_FILE = 'financial_history.json'
FILES_LIST_FILE = 'loaded_files.json'

# =============================================================================
# دوال حفظ وتحميل البيانات
# =============================================================================
def save_data(data, history):
    """حفظ البيانات وسجل التعديلات"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ البيانات: {str(e)}")
        return False

def save_files_list(files_list):
    """حفظ قائمة الملفات المحملة"""
    try:
        with open(FILES_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(files_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ قائمة الملفات: {str(e)}")
        return False

def load_saved_data():
    """تحميل البيانات المحفوظة"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        return None
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {str(e)}")
        return None

def load_history():
    """تحميل سجل التعديلات"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"خطأ في تحميل السجل: {str(e)}")
        return []

def load_files_list():
    """تحميل قائمة الملفات المحملة"""
    try:
        if os.path.exists(FILES_LIST_FILE):
            with open(FILES_LIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"خطأ في تحميل قائمة الملفات: {str(e)}")
        return []

def add_to_history(action, details):
    """إضافة حدث لسجل التعديلات"""
    try:
        history = load_history()
        history.insert(0, {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        })
        history = history[:100]
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"خطأ في إضافة للسجل: {str(e)}")
        return False

# =============================================================================
# دالة قراءة ملف Excel
# =============================================================================
def load_excel_file(file):
    """قراءة ملف Excel وتحويله إلى DataFrame"""
    try:
        df = pd.read_excel(file, sheet_name='بيانات')
        
        header_idx = None
        for idx, row in df.iterrows():
            if 'التاريخ' in str(row.values):
                header_idx = idx
                break
        
        if header_idx is None:
            st.error("لم يتم العثور على عناوين الأعمدة في الملف")
            return None
        
        df = pd.read_excel(file, sheet_name='بيانات', header=header_idx)
        df = df.dropna(how='all')
        df = df[df['التاريخ'].notna()]
        
        df['مصروف'] = pd.to_numeric(df['مصروف'], errors='coerce').fillna(0)
        df['ايراد'] = pd.to_numeric(df['ايراد'], errors='coerce').fillna(0)
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        
        df['addedBy'] = ''
        df['addedTimestamp'] = ''
        df['addedManually'] = False
        
        return df
        
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {str(e)}")
        return None

# =============================================================================
# دالة حساب الإحصائيات
# =============================================================================
def calculate_statistics(df):
    """حساب الإحصائيات المالية"""
    try:
        total_revenue = float(df['ايراد'].sum())
        total_expense = float(df['مصروف'].sum())
        net_profit = total_revenue - total_expense
        total_transactions = len(df)
        
        return {
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'total_transactions': total_transactions
        }
    except Exception as e:
        st.error(f"خطأ في حساب الإحصائيات: {str(e)}")
        return {
            'total_revenue': 0,
            'total_expense': 0,
            'net_profit': 0,
            'total_transactions': 0
        }

# =============================================================================
# دالة عرض الرسوم البيانية
# =============================================================================
def display_charts(df):
    """عرض الرسوم البيانية"""
    try:
        st.subheader("📊 الإيرادات والمصروفات الشهرية")
        monthly_data = df.groupby('الشهر').agg({
            'ايراد': 'sum',
            'مصروف': 'sum'
        }).reset_index()
        
        month_order = ['يناير', 'فبراير', 'مارس', 'ابريل', 'مايو', 'يونيو', 
                       'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        monthly_data['الشهر'] = pd.Categorical(monthly_data['الشهر'], categories=month_order, ordered=True)
        monthly_data = monthly_data.sort_values('الشهر')
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=monthly_data['الشهر'],
            y=monthly_data['ايراد'],
            name='الإيرادات',
            marker_color='rgba(17, 153, 142, 0.8)'
        ))
        fig1.add_trace(go.Bar(
            x=monthly_data['الشهر'],
            y=monthly_data['مصروف'],
            name='المصروفات',
            marker_color='rgba(235, 51, 73, 0.8)'
        ))
        fig1.update_layout(
            barmode='group',
            xaxis_title='الشهر',
            yaxis_title='المبلغ (ريال)',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 توزيع المصروفات حسب النوع")
            expense_data = df[df['مصروف'] > 0].groupby('الحساب')['مصروف'].sum().sort_values(ascending=False).head(10)
            
            if len(expense_data) > 0:
                fig2 = px.pie(
                    values=expense_data.values,
                    names=expense_data.index,
                    hole=0.4
                )
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("لا توجد بيانات مصروفات لعرضها")
        
        with col2:
            st.subheader("🥧 توزيع الإيرادات حسب النوع")
            revenue_data = df[df['ايراد'] > 0].groupby('الحساب')['ايراد'].sum().sort_values(ascending=False).head(10)
            
            if len(revenue_data) > 0:
                fig3 = px.pie(
                    values=revenue_data.values,
                    names=revenue_data.index,
                    hole=0.4
                )
                fig3.update_traces(textposition='inside', textinfo='percent+label')
                fig3.update_layout(height=400)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("لا توجد بيانات إيرادات لعرضها")
        
        st.subheader("📈 تطور صافي الربح الشهري")
        monthly_data['صافي_الربح'] = monthly_data['ايراد'] - monthly_data['مصروف']
        
        fig4 = px.line(
            monthly_data,
            x='الشهر',
            y='صافي_الربح',
            markers=True,
            line_shape='spline'
        )
        fig4.update_traces(
            line_color='rgba(245, 87, 108, 1)',
            fill='tozeroy',
            fillcolor='rgba(240, 147, 251, 0.2)'
        )
        fig4.update_layout(
            xaxis_title='الشهر',
            yaxis_title='صافي الربح (ريال)',
            height=400
        )
        st.plotly_chart(fig4, use_container_width=True)
        
    except Exception as e:
        st.error(f"خطأ في عرض الرسوم البيانية: {str(e)}")

# =============================================================================
# التهيئة
# =============================================================================
if 'df' not in st.session_state:
    saved_df = load_saved_data()
    if saved_df is not None:
        st.session_state.df = saved_df
    else:
        st.session_state.df = None

if 'loaded_files' not in st.session_state:
    st.session_state.loaded_files = load_files_list()

# =============================================================================
# العنوان الرئيسي
# =============================================================================
st.title("📊 لوحة الإيرادات والمصروفات 2025")
st.markdown("### نظام إدارة وتحليل البيانات المالية")

# =============================================================================
# الشريط الجانبي
# =============================================================================
with st.sidebar:
    st.header("⚙️ القائمة الرئيسية")
    
    st.subheader("📁 رفع ملفات البيانات")
    
    uploaded_file = st.file_uploader(
        "اختر ملف Excel (أو عدة ملفات)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="ارفع ملف أو عدة ملفات Excel التي تحتوي على شيت 'بيانات'"
    )
    
    if uploaded_file:
        for file in uploaded_file:
            if file.name not in [f['name'] for f in st.session_state.loaded_files]:
                df_new = load_excel_file(file)
                if df_new is not None:
                    st.session_state.loaded_files.append({
                        'name': file.name,
                        'rows': len(df_new),
                        'date': datetime.now().isoformat()
                    })
                    
                    save_files_list(st.session_state.loaded_files)
                    
                    if st.session_state.df is None:
                        st.session_state.df = df_new
                    else:
                        st.session_state.df = pd.concat([st.session_state.df, df_new], 
                                                        ignore_index=True)
                    
                    save_data(st.session_state.df.to_dict('records'), load_history())
                    add_to_history('تحميل ملف', f'تم تحميل {len(df_new)} عملية من {file.name}')
                    st.success(f"✅ {file.name}: تم تحميل {len(df_new)} عملية")
    
    if st.session_state.loaded_files:
        st.divider()
        st.subheader("📚 الملفات المحملة")
        for idx, file_info in enumerate(st.session_state.loaded_files):
            with st.expander(f"📄 {file_info['name']}", expanded=False):
                st.write(f"**عدد العمليات:** {file_info['rows']}")
                file_date = datetime.fromisoformat(file_info['date'])
                st.write(f"**تاريخ التحميل:** {file_date.strftime('%Y-%m-%d %H:%M')}")
                
                if st.button(f"🗑️ حذف", key=f"delete_{idx}"):
                    st.session_state.loaded_files.pop(idx)
                    save_files_list(st.session_state.loaded_files)
                    st.success(f"تم حذف {file_info['name']} من القائمة")
                    st.rerun()
    
    st.divider()
    
    page = st.radio(
        "اختر الصفحة",
        ["📈 لوحة التحكم", "📋 البيانات", "➕ إضافة جديدة", "📜 السجل", "💾 التصدير", "📂 إدارة الملفات"],
        label_visibility="collapsed"
    )

# =============================================================================
# التحقق من وجود بيانات
# =============================================================================
if st.session_state.df is None:
    st.info("👆 الرجاء رفع ملف Excel من القائمة الجانبية للبدء")
    st.stop()

df = st.session_state.df

# =============================================================================
# صفحة لوحة التحكم
# =============================================================================
if page == "📈 لوحة التحكم":
    stats = calculate_statistics(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 إجمالي الإيرادات",
            value=f"{stats['total_revenue']:,.2f} ريال"
        )
    
    with col2:
        st.metric(
            label="💸 إجمالي المصروفات",
            value=f"{stats['total_expense']:,.2f} ريال"
        )
    
    with col3:
        st.metric(
            label="📊 صافي الربح",
            value=f"{stats['net_profit']:,.2f} ريال"
        )
    
    with col4:
        st.metric(
            label="📝 عدد العمليات",
            value=f"{stats['total_transactions']:,}"
        )
    
    st.divider()
    display_charts(df)

# =============================================================================
# صفحة البيانات
# =============================================================================
elif page == "📋 البيانات":
    st.header("📋 جدول البيانات التفصيلي")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        months = ['الكل'] + sorted(df['الشهر'].dropna().unique().tolist())
        selected_month = st.selectbox("الشهر", months)
    
    with col2:
        accounts = ['الكل'] + sorted(df['الحساب'].dropna().unique().tolist())
        selected_account = st.selectbox("الحساب", accounts)
    
    with col3:
        transaction_types = ['الكل', 'إيرادات', 'مصروفات']
        selected_type = st.selectbox("نوع العملية", transaction_types)
    
    filtered_df = df.copy()
    
    if selected_month != 'الكل':
        filtered_df = filtered_df[filtered_df['الشهر'] == selected_month]
    
    if selected_account != 'الكل':
        filtered_df = filtered_df[filtered_df['الحساب'] == selected_account]
    
    if selected_type == 'إيرادات':
        filtered_df = filtered_df[filtered_df['ايراد'] > 0]
    elif selected_type == 'مصروفات':
        filtered_df = filtered_df[filtered_df['مصروف'] > 0]
    
    st.write(f"عدد العمليات المعروضة: {len(filtered_df)}")
    
    display_df = filtered_df.copy()
    display_df['التاريخ'] = pd.to_datetime(display_df['التاريخ']).dt.strftime('%Y-%m-%d')
    
    columns_to_display = ['التاريخ', 'الشهر', 'الحساب', 'النوع', 'وصف العملية', 
                         'المرجع', 'مصروف', 'ايراد', 'addedBy', 'addedTimestamp']
    
    column_names = {
        'التاريخ': 'التاريخ',
        'الشهر': 'الشهر',
        'الحساب': 'الحساب',
        'النوع': 'النوع',
        'وصف العملية': 'الوصف',
        'المرجع': 'المرجع',
        'مصروف': 'المصروف',
        'ايراد': 'الإيراد',
        'addedBy': 'المضيف',
        'addedTimestamp': 'تاريخ الإضافة'
    }
    
    display_df = display_df[columns_to_display].rename(columns=column_names)
    display_df['المصروف'] = display_df['المصروف'].apply(lambda x: f"{x:,.2f}")
    display_df['الإيراد'] = display_df['الإيراد'].apply(lambda x: f"{x:,.2f}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600
    )

# =============================================================================
# صفحة الإضافة
# =============================================================================
elif page == "➕ إضافة جديدة":
    st.header("➕ إضافة عملية مالية جديدة")
    
    with st.form("add_transaction_form", clear_on_submit=True):
        st.subheader("معلومات العملية")
        
        col1, col2 = st.columns(2)
        
        with col1:
            added_by = st.text_input("اسم المستخدم (من يقوم بالإضافة) *", 
                                     placeholder="أدخل اسمك")
            transaction_date = st.date_input("تاريخ العملية *", 
                                            value=date.today())
            
            months = ['', 'يناير', 'فبراير', 'مارس', 'ابريل', 'مايو', 'يونيو',
                     'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
            selected_month = st.selectbox("الشهر *", months)
            
            existing_accounts = sorted(df['الحساب'].dropna().unique().tolist())
            account = st.selectbox("الحساب *", [''] + existing_accounts)
            
            if account == '':
                account = st.text_input("أو أدخل اسم حساب جديد")
        
        with col2:
            payment_types = ['', 'نقدي', 'نقدا', 'بنكي', 'شيك', 'تحويل']
            payment_type = st.selectbox("نوع الدفع *", payment_types)
            
            description = st.text_area("وصف العملية *", 
                                      placeholder="أدخل وصف تفصيلي للعملية",
                                      height=100)
            
            reference = st.text_input("المرجع", 
                                     placeholder="رقم المرجع أو الفاتورة")
        
        st.divider()
        
        col3, col4 = st.columns(2)
        
        with col3:
            transaction_type = st.radio("نوع العملية *", 
                                       ['إيراد', 'مصروف'],
                                       horizontal=True)
        
        with col4:
            amount = st.number_input("المبلغ *", 
                                    min_value=0.0, 
                                    value=0.0,
                                    step=0.01,
                                    format="%.2f")
        
        submitted = st.form_submit_button("💾 حفظ العملية", 
                                         type="primary",
                                         use_container_width=True)
        
        if submitted:
            if not added_by or not selected_month or not account or not payment_type or not description or amount <= 0:
                st.error("⚠️ الرجاء ملء جميع الحقول المطلوبة وإدخال مبلغ أكبر من صفر")
            else:
                new_transaction = {
                    'التاريخ': pd.Timestamp(transaction_date),
                    'الشهر': selected_month,
                    'الحساب': account,
                    'النوع': payment_type,
                    'وصف العملية': description,
                    'المرجع': reference,
                    'مصروف': amount if transaction_type == 'مصروف' else 0,
                    'ايراد': amount if transaction_type == 'إيراد' else 0,
                    'addedBy': added_by,
                    'addedTimestamp': datetime.now().isoformat(),
                    'addedManually': True
                }
                
                new_df = pd.DataFrame([new_transaction])
                st.session_state.df = pd.concat([st.session_state.df, new_df], 
                                                ignore_index=True)
                
                save_data(st.session_state.df.to_dict('records'), load_history())
                
                history_details = f"{transaction_type} - {account} - {amount:,.2f} ريال - بواسطة {added_by}"
                add_to_history('إضافة عملية جديدة', history_details)
                
                st.success(f"✅ تمت إضافة العملية بنجاح! ({transaction_type}: {amount:,.2f} ريال)")
                st.balloons()

# =============================================================================
# صفحة السجل
# =============================================================================
elif page == "📜 السجل":
    st.header("📜 سجل التعديلات والإضافات")
    
    history = load_history()
    
    if not history:
        st.info("لا توجد سجلات بعد")
    else:
        for item in history:
            timestamp = datetime.fromisoformat(item['timestamp'])
            formatted_date = timestamp.strftime('%Y-%m-%d')
            formatted_time = timestamp.strftime('%H:%M:%S')
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{item['action']}**")
                    st.text(item['details'])
                with col2:
                    st.text(formatted_date)
                    st.text(formatted_time)
                st.divider()

# =============================================================================
# صفحة التصدير
# =============================================================================
elif page == "💾 التصدير":
    st.header("💾 تصدير وإدارة البيانات")
    
    st.subheader("📥 تصدير البيانات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**تصدير إلى Excel**")
        
        export_df = df.copy()
        export_df['التاريخ'] = pd.to_datetime(export_df['التاريخ']).dt.strftime('%Y-%m-%d')
        
        export_columns = ['التاريخ', 'الشهر', 'الحساب', 'النوع', 'وصف العملية',
                         'المرجع', 'مصروف', 'ايراد', 'addedBy', 'addedTimestamp']
        export_df = export_df[export_columns]
        
        export_df.columns = ['التاريخ', 'الشهر', 'الحساب', 'النوع', 'الوصف',
                            'المرجع', 'المصروف', 'الإيراد', 'المضيف', 'تاريخ الإضافة']
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='بيانات', index=False)
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 تحميل ملف Excel",
            data=excel_data,
            file_name=f"الايرادات_والمصروفات_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        st.write("**تصدير إلى JSON**")
        
        json_data = df.to_json(orient='records', force_ascii=False, indent=2)
        
        st.download_button(
            label="📄 تحميل ملف JSON",
            data=json_data,
            file_name=f"الايرادات_والمصروفات_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    st.divider()
    
    st.subheader("🗑️ إدارة البيانات")
    st.warning("⚠️ تحذير: هذه العمليات لا يمكن التراجع عنها!")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.write("**حذف البيانات المضافة يدوياً**")
        if st.button("🔄 حذف البيانات المضافة فقط", 
                    use_container_width=True):
            before_count = len(df)
            st.session_state.df = df[df['addedManually'] == False]
            after_count = len(st.session_state.df)
            deleted_count = before_count - after_count
            
            save_data(st.session_state.df.to_dict('records'), load_history())
            add_to_history('حذف البيانات المضافة', f'تم حذف {deleted_count} عملية مضافة يدوياً')
            
            st.success(f"✅ تم حذف {deleted_count} عملية مضافة")
            st.rerun()
    
    with col4:
        st.write("**حذف جميع البيانات**")
        if st.button("⚠️ حذف جميع البيانات", 
                    use_container_width=True):
            count = len(df)
            st.session_state.df = None
            
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            
            st.success(f"✅ تم حذف {count} عملية")
            st.info("الرجاء رفع ملف Excel جديد للبدء")
            st.rerun()

# =============================================================================
# صفحة إدارة الملفات
# =============================================================================
elif page == "📂 إدارة الملفات":
    st.header("📂 إدارة ملفات Excel المحملة")
    
    if not st.session_state.loaded_files:
        st.info("📭 لم يتم تحميل أي ملفات بعد. استخدم القائمة الجانبية لرفع ملفات Excel.")
    else:
        st.write(f"**إجمالي الملفات المحملة:** {len(st.session_state.loaded_files)}")
        st.write(f"**إجمالي العمليات:** {len(df) if df is not None else 0}")
        
        st.divider()
        
        st.subheader("📊 قائمة الملفات")
        
        files_data = []
        for file_info in st.session_state.loaded_files:
            file_date = datetime.fromisoformat(file_info['date'])
            files_data.append({
                'اسم الملف': file_info['name'],
                'عدد العمليات': file_info['rows'],
                'تاريخ التحميل': file_date.strftime('%Y-%m-%d %H:%M')
            })
        
        if files_data:
            files_df = pd.DataFrame(files_data)
            st.dataframe(files_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.subheader("⚙️ خيارات متقدمة")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**إعادة تحميل جميع الملفات**")
            if st.button("🔄 إعادة تحميل", use_container_width=True):
                st.session_state.loaded_files = []
                st.session_state.df = None
                save_data([], load_history())
                save_files_list([])
                st.success("✅ تم مسح قائمة الملفات. يمكنك رفع ملفات جديدة.")
                st.rerun()
        
        with col2:
            st.write("**مسح السجل**")
            if st.button("🗑️ مسح السجل", use_container_width=True):
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                st.success("✅ تم مسح السجل")
                st.rerun()
        
        with col3:
            st.write("**إحصائيات سريعة**")
            if df is not None:
                st.metric("عدد الأشهر", len(df['الشهر'].unique()))
                st.metric("عدد الحسابات", len(df['الحساب'].unique()))
        
        st.divider()
        
        st.subheader("🔍 فحص التكرارات")
        
        if df is not None:
            duplicate_cols = ['التاريخ', 'الحساب', 'مصروف', 'ايراد']
            duplicates = df[df.duplicated(subset=duplicate_cols, keep=False)]
            
            if len(duplicates) > 0:
                st.warning(f"⚠️ تم العثور على {len(duplicates)} عملية مكررة محتملة")
                
                if st.checkbox("عرض العمليات المكررة"):
                    display_dup = duplicates.copy()
                    display_dup['التاريخ'] = pd.to_datetime(display_dup['التاريخ']).dt.strftime('%Y-%m-%d')
                    
                    cols_to_show = ['التاريخ', 'الشهر', 'الحساب', 'وصف العملية', 'مصروف', 'ايراد']
                    st.dataframe(
                        display_dup[cols_to_show],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if st.button("🗑️ حذف التكرارات تلقائياً", type="secondary"):
                        before = len(st.session_state.df)
                        st.session_state.df = df.drop_duplicates(subset=duplicate_cols, keep='first')
                        after = len(st.session_state.df)
                        removed = before - after
                        
                        save_data(st.session_state.df.to_dict('records'), load_history())
                        add_to_history('حذف التكرارات', f'تم حذف {removed} عملية مكررة')
                        
                        st.success(f"✅ تم حذف {removed} عملية مكررة")
                        st.rerun()
            else:
                st.success("✅ لا توجد عمليات مكررة")
        
        st.divider()
        
        st.subheader("🔗 دمج البيانات من مصادر متعددة")
        st.info("""
        💡 **نصائح:**
        - يمكنك رفع عدة ملفات Excel مختلفة
        - سيتم دمج جميع البيانات تلقائياً
        - تأكد من أن جميع الملفات تحتوي على نفس بنية الأعمدة
        - استخدم خاصية "فحص التكرارات" لتنظيف البيانات المكررة
        """)

# =============================================================================
# معلومات إضافية في الشريط الجانبي
# =============================================================================
with st.sidebar:
    st.divider()
    st.caption("💡 تطوير: نظام إدارة مالية متكامل")
    st.caption(f"📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if st.session_state.df is not None:
        manual_count = len(df[df['addedManually'] == True])
        original_count = len(df[df['addedManually'] == False])
        st.caption(f"📊 البيانات الأصلية: {original_count}")
        st.caption(f"➕ البيانات المضافة: {manual_count}")
