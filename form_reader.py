import streamlit as st
import json
import uuid
from typing import List, Dict, Any
from pyairtable import Api
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Form Reader",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'current_event_id' not in st.session_state:
    st.session_state.current_event_id = None
if 'form_loaded' not in st.session_state:
    st.session_state.form_loaded = False

# Airtable configuration
AIRTABLE_CONFIG = {
    "base_id": "applJyRTlJLvUEDJs",
    "api_key": "patJHZQyID8nmSaxh.1bcf08f100bd723fd85d67eff8534a19f951b75883d0e0ae4cc49743a9fb3131"
}

# Data type options mapping
DATA_TYPES = {
    "text": "Yazı",
    "number": "Sayı", 
    "float": "Virgüllü sayı",
    "date": "Tarih",
    "datetime": "Saat ve tarih",
    "boolean": "Doğru yanlış",
    "single_choice": "Çoktan seçmeli",
    "multiple_choice": "Çoktan seçmeli çoklu cevap"
}

def get_airtable_api():
    """Get Airtable API instance"""
    return Api(AIRTABLE_CONFIG["api_key"])

def get_airtable_table(table_name):
    """Get Airtable table instance"""
    api = get_airtable_api()
    return api.table(AIRTABLE_CONFIG["base_id"], table_name)

def load_forms():
    """Load all available forms from Airtable"""
    try:
        table = get_airtable_table("registration_form")
        records = table.all()
        
        # Group by event_id
        forms = {}
        for record in records:
            event_id = record['fields'].get('event_id')
            if event_id not in forms:
                forms[event_id] = []
            
            forms[event_id].append({
                'id': int(record['fields'].get('id', 0)),  # Convert to integer
                'name': record['fields'].get('name', ''),
                'type': record['fields'].get('type', 'text'),
                'is_required': record['fields'].get('is_required', False),
                'rank': record['fields'].get('rank', 0),
                'possible_answers': record['fields'].get('possible_answers', '[]')
            })
        
        # Sort questions by rank within each form
        for event_id in forms:
            forms[event_id].sort(key=lambda x: x['rank'])
        
        return forms
    except Exception as e:
        st.error(f"Formlar yüklenirken hata oluştu: {str(e)}")
        return {}



def render_form_question(question):
    """Render a form question based on its type"""
    question_id = question['id']
    question_text = question['name']
    question_type = question['type']
    is_required = question['is_required']
    
    # Add required indicator
    if is_required:
        question_text += " *"
    
    st.markdown(f"**{question_text}**")
    
    # Render different input types
    if question_type == "text":
        answer = st.text_input("Cevabınız:", key=f"input_{question_id}")
        if is_required and not answer:
            st.error("Bu alan zorunludur!")
        return answer
    
    elif question_type == "number":
        answer = st.number_input("Cevabınız:", key=f"input_{question_id}")
        if is_required and answer is None:
            st.error("Bu alan zorunludur!")
        return answer
    
    elif question_type == "float":
        answer = st.number_input("Cevabınız:", step=0.1, key=f"input_{question_id}")
        if is_required and answer is None:
            st.error("Bu alan zorunludur!")
        return answer
    
    elif question_type == "date":
        answer = st.date_input("Cevabınız:", key=f"input_{question_id}")
        if is_required and answer is None:
            st.error("Bu alan zorunludur!")
        return answer
    
    elif question_type == "datetime":
        # Separate date and time selection for better clarity
        col_date, col_time = st.columns(2)
        
        with col_date:
            date_answer = st.date_input("Tarih:", key=f"date_{question_id}")
        
        with col_time:
            time_answer = st.time_input("Saat:", key=f"time_{question_id}")
        
        # Combine date and time
        if date_answer and time_answer:
            answer = f"{date_answer} {time_answer}"
        else:
            answer = None
            
        if is_required and not answer:
            st.error("Bu alan zorunludur!")
        return answer
    
    elif question_type == "boolean":
        answer = st.radio("Cevabınız:", ["Evet", "Hayır"], key=f"input_{question_id}")
        if is_required and not answer:
            st.error("Bu alan zorunludur!")
        return answer
    
    elif question_type == "single_choice":
        try:
            options = json.loads(question['possible_answers'])
            if options:
                answer = st.radio("Cevabınız:", options, key=f"input_{question_id}")
                if is_required and not answer:
                    st.error("Bu alan zorunludur!")
                return answer
            else:
                st.error("Bu soru için seçenek bulunamadı!")
                return None
        except:
            st.error("Seçenekler yüklenirken hata oluştu!")
            return None
    
    elif question_type == "multiple_choice":
        try:
            options = json.loads(question['possible_answers'])
            if options:
                answer = st.multiselect("Cevabınız:", options, key=f"input_{question_id}")
                if is_required and not answer:
                    st.error("Bu alan zorunludur!")
                return answer
            else:
                st.error("Bu soru için seçenek bulunamadı!")
                return None
        except:
            st.error("Seçenekler yüklenirken hata oluştu!")
            return None
    
    return None

def save_answers(event_id, answers):
    """Save form answers to Airtable"""
    try:
        # Save form answers
        table = get_airtable_table("registration_form_answers")
        
        # Generate a unique user_id for this submission
        user_id = str(uuid.uuid4())
        
        # Create a record for each answer
        for question_id, answer in answers.items():
            if answer is not None and answer != "":
                record_data = {
                    "registration_form_id": int(question_id),  # Convert to integer for number column
                    "user_id": user_id,
                    "answer": str(answer) if not isinstance(answer, list) else json.dumps(answer)
                }
                
                table.create(record_data)
        
        st.success("Form başarıyla gönderildi!")
        return True
        
    except Exception as e:
        st.error(f"Form gönderilirken hata oluştu: {str(e)}")
        return False

def main():
    st.title("📋 Form Doldurucu")
    st.markdown("Event ID'si girerek ilgili formu doldurun.")
    
    # Event ID input section
    if not st.session_state.form_loaded:
        st.header("Event ID Girişi")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            event_id = st.text_input(
                "Event ID girin (örnek: 22):",
                placeholder="22",
                help="Doldurmak istediğiniz formun event ID'sini girin"
            )
        
        with col2:
            apply_button = st.button("Uygula", type="primary", use_container_width=True)
        
        if event_id and apply_button:
            # Load forms
            forms = load_forms()
            
            if not forms:
                st.warning("Henüz hiç form oluşturulmamış.")
                return
            
            # Check if event_id exists in forms
            if event_id in forms:
                questions = forms[event_id]
                
                if questions:
                    # Store event ID and mark form as loaded
                    st.session_state.current_event_id = event_id
                    st.session_state.form_loaded = True
                    st.rerun()
                else:
                    st.warning(f"Event ID {event_id} için soru bulunamadı.")
            else:
                st.error(f"Event ID {event_id} için form bulunamadı. Lütfen geçerli bir Event ID girin.")
    
    # Form display section
    else:
        # Show current event ID and option to change
        st.header(f"Event {st.session_state.current_event_id} Formu")
        
        # Add a button to go back to event ID input
        if st.button("🔄 Farklı Event ID Gir", type="secondary"):
            st.session_state.form_loaded = False
            st.session_state.current_event_id = None
            st.session_state.answers = {}
            st.rerun()
        
        # Load and display form
        forms = load_forms()
        if forms and st.session_state.current_event_id in forms:
            questions = forms[st.session_state.current_event_id]
            
            if questions:
                st.markdown("---")
                
                # Display form questions
                answers = {}
                
                for question in questions:
                    with st.container():
                        st.markdown("---")
                        answer = render_form_question(question)
                        answers[question['id']] = answer
                
                # Submit button
                st.markdown("---")
                if st.button("📤 Formu Gönder", type="primary", use_container_width=True):
                    # Check if all required fields are filled
                    required_fields_missing = False
                    for question in questions:
                        if question['is_required'] and (answers.get(question['id']) is None or answers.get(question['id']) == ""):
                            required_fields_missing = True
                            break
                    
                    if required_fields_missing:
                        st.error("Lütfen tüm zorunlu alanları doldurun!")
                    else:
                        if save_answers(st.session_state.current_event_id, answers):
                            # Clear form and show success
                            st.session_state.answers = {}
                            st.success("Form başarıyla gönderildi!")
                            # Reset to event ID input
                            st.session_state.form_loaded = False
                            st.session_state.current_event_id = None
                            st.rerun()
            else:
                st.warning(f"Event ID {st.session_state.current_event_id} için soru bulunamadı.")
        else:
            st.error(f"Event ID {st.session_state.current_event_id} için form bulunamadı.")
            if st.button("🔄 Yeni Event ID Gir"):
                st.session_state.form_loaded = False
                st.session_state.current_event_id = None
                st.rerun()

if __name__ == "__main__":
    main() 