"""
Medical AI Configuration

Configuration settings for BioGPT and PubMedGPT models.
"""

import os
from typing import Dict, Any


class MedicalAIConfig:
    """Configuration for medical AI models."""
    
    # Model configurations
    BIOGPT_CONFIG = {
        "model_name": "microsoft/BioGPT",
        "max_length": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": True,
        "num_return_sequences": 1,
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_use_double_quant": True,
    }
    
    PUBMEDGPT_CONFIG = {
        "model_name": "stanford-crfm/BioMedLM",
        "max_length": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": True,
        "num_return_sequences": 1,
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_use_double_quant": True,
    }
    
    # Medical analysis prompts
    MEDICAL_ANALYSIS_PROMPT = """
You are a medical AI assistant analyzing health-related images and medical cases. 
Please provide a comprehensive medical assessment including:

1. **Possible Medical Conditions**: Identify potential diagnoses based on the presented information
2. **Severity Assessment**: Evaluate the severity level (mild, moderate, severe)
3. **Urgency Level**: Determine urgency (low, normal, high, emergency)
4. **Differential Diagnosis**: List possible alternative diagnoses
5. **Recommended Next Steps**: Suggest appropriate medical actions
6. **Treatment Recommendations**: Provide detailed treatment protocols including:
   - Specific medications, creams, gels, or treatments
   - Dosages and application frequencies
   - Step-by-step treatment instructions
   - Duration of treatment
   - Precautions and contraindications
   - Potential side effects
   - When to stop treatment
   - Follow-up requirements
   - Lifestyle modifications
   - Diet recommendations
   - Prevention strategies

Please respond in a structured medical format suitable for clinical assessment.
Focus on evidence-based medical knowledge and clinical guidelines.
Provide specific, actionable treatment recommendations based on current medical research.
"""
    
    # Medical condition categories and keywords
    MEDICAL_CONDITIONS = {
        "skin": [
            "rash", "burn", "dermatitis", "eczema", "psoriasis", "acne", "mole", "lesion",
            "hives", "urticaria", "rosacea", "vitiligo", "melanoma", "basal_cell_carcinoma",
            "squamous_cell_carcinoma", "fungal_infection", "bacterial_infection", "viral_infection",
            "contact_dermatitis", "atopic_dermatitis", "seborrheic_dermatitis", "lichen_planus",
            "pityriasis_rosea", "tinea", "ringworm", "impetigo", "cellulitis", "folliculitis",
            "hidradenitis_suppurativa", "keratosis_pilaris", "actinic_keratosis", "dermatofibroma"
        ],
        "injury": [
            "cut", "wound", "bruise", "fracture", "sprain", "strain", "dislocation",
            "concussion", "laceration", "abrasion", "puncture", "avulsion", "amputation",
            "contusion", "hematoma", "whiplash", "torn_ligament", "torn_tendon", "compartment_syndrome",
            "crush_injury", "penetrating_wound", "gunshot_wound", "stab_wound", "burns_thermal",
            "burns_chemical", "burns_electrical", "frostbite", "heat_exhaustion", "heat_stroke"
        ],
        "eye": [
            "conjunctivitis", "stye", "cataract", "glaucoma", "macular_degeneration",
            "retinal_detachment", "corneal_abrasion", "uveitis", "blepharitis", "dry_eye",
            "keratitis", "iritis", "scleritis", "optic_neuritis", "diabetic_retinopathy",
            "hypertensive_retinopathy", "retinal_vein_occlusion", "retinal_artery_occlusion",
            "vitreous_hemorrhage", "retinal_tear", "floaters", "eye_strain", "amblyopia",
            "strabismus", "nystagmus", "ptosis", "entropion", "ectropion", "chalazion"
        ],
        "dental": [
            "cavity", "gum_disease", "gingivitis", "periodontitis", "tooth_abscess",
            "tooth_fracture", "dental_caries", "oral_cancer", "mouth_ulcer", "toothache",
            "dental_erosion", "tooth_sensitivity", "malocclusion", "bruxism", "tmj_disorder",
            "oral_thrush", "leukoplakia", "erythroplakia", "oral_lichen_planus", "geographic_tongue",
            "fissured_tongue", "black_hairy_tongue", "gingival_recession", "dental_plaque",
            "tartar", "halitosis", "xerostomia", "sialadenitis", "ranula", "mucocele"
        ],
        "respiratory": [
            "pneumonia", "bronchitis", "asthma", "copd", "pulmonary_embolism",
            "pleural_effusion", "pneumothorax", "tuberculosis", "lung_cancer",
            "bronchiectasis", "cystic_fibrosis", "pulmonary_fibrosis", "sarcoidosis",
            "pulmonary_hypertension", "sleep_apnea", "bronchiolitis", "croup", "epiglottitis",
            "pleurisy", "empyema", "lung_abscess", "pulmonary_nodule", "mesothelioma",
            "pulmonary_edema", "acute_respiratory_distress_syndrome", "pulmonary_contusion"
        ],
        "gastrointestinal": [
            "gastritis", "ulcer", "appendicitis", "cholecystitis", "pancreatitis",
            "hepatitis", "cirrhosis", "inflammatory_bowel_disease", "colorectal_cancer",
            "gastroesophageal_reflux_disease", "peptic_ulcer_disease", "celiac_disease",
            "irritable_bowel_syndrome", "crohns_disease", "ulcerative_colitis", "diverticulitis",
            "gallstones", "pancreatic_cancer", "liver_cancer", "esophageal_cancer",
            "stomach_cancer", "gastroparesis", "intestinal_obstruction", "volvulus",
            "intussusception", "peritonitis", "ascites", "jaundice", "hepatic_encephalopathy"
        ],
        "cardiac": [
            "myocardial_infarction", "angina", "heart_failure", "arrhythmia",
            "hypertension", "cardiomyopathy", "pericarditis", "endocarditis",
            "atrial_fibrillation", "ventricular_fibrillation", "bradycardia", "tachycardia",
            "heart_block", "coronary_artery_disease", "aortic_aneurysm", "aortic_dissection",
            "valvular_heart_disease", "mitral_valve_prolapse", "aortic_stenosis",
            "congestive_heart_failure", "cardiogenic_shock", "myocarditis", "pericardial_effusion",
            "cardiac_tamponade", "pulmonary_embolism", "deep_vein_thrombosis", "varicose_veins"
        ],
        "neurological": [
            "stroke", "migraine", "epilepsy", "meningitis", "encephalitis",
            "multiple_sclerosis", "parkinsons_disease", "alzheimers_disease",
            "transient_ischemic_attack", "subarachnoid_hemorrhage", "intracerebral_hemorrhage",
            "brain_tumor", "hydrocephalus", "normal_pressure_hydrocephalus", "bell_palsy",
            "trigeminal_neuralgia", "sciatica", "carpal_tunnel_syndrome", "guillain_barre_syndrome",
            "amyotrophic_lateral_sclerosis", "huntingtons_disease", "dementia", "delirium",
            "concussion", "traumatic_brain_injury", "spinal_cord_injury", "peripheral_neuropathy"
        ],
        "musculoskeletal": [
            "arthritis", "osteoarthritis", "rheumatoid_arthritis", "gout", "fibromyalgia",
            "osteoporosis", "osteomyelitis", "tendonitis", "bursitis", "carpal_tunnel_syndrome",
            "herniated_disc", "scoliosis", "kyphosis", "lordosis", "spinal_stenosis",
            "ankylosing_spondylitis", "polymyalgia_rheumatica", "temporal_arteritis",
            "myositis", "muscular_dystrophy", "myasthenia_gravis", "compartment_syndrome",
            "stress_fracture", "avascular_necrosis", "bone_tumor", "metastatic_bone_disease"
        ],
        "endocrine": [
            "diabetes_mellitus", "diabetes_insipidus", "hyperthyroidism", "hypothyroidism",
            "graves_disease", "hashimotos_thyroiditis", "thyroid_nodule", "thyroid_cancer",
            "addisons_disease", "cushings_syndrome", "pheochromocytoma", "acromegaly",
            "dwarfism", "gigantism", "hyperparathyroidism", "hypoparathyroidism",
            "adrenal_insufficiency", "adrenal_tumor", "pituitary_tumor", "insulinoma",
            "glucagonoma", "metabolic_syndrome", "polycystic_ovary_syndrome"
        ],
        "hematological": [
            "anemia", "iron_deficiency_anemia", "vitamin_b12_deficiency", "folate_deficiency",
            "sickle_cell_anemia", "thalassemia", "leukemia", "lymphoma", "multiple_myeloma",
            "hemophilia", "von_willebrand_disease", "thrombocytopenia", "thrombocytosis",
            "polycythemia_vera", "myelodysplastic_syndrome", "aplastic_anemia",
            "hemolytic_anemia", "autoimmune_hemolytic_anemia", "g6pd_deficiency",
            "disseminated_intravascular_coagulation", "deep_vein_thrombosis", "pulmonary_embolism"
        ],
        "immunological": [
            "allergic_reaction", "anaphylaxis", "hay_fever", "food_allergy", "drug_allergy",
            "latex_allergy", "hiv_aids", "lupus", "rheumatoid_arthritis", "sjogrens_syndrome",
            "scleroderma", "vasculitis", "sarcoidosis", "immunodeficiency", "autoimmune_disease",
            "graft_versus_host_disease", "transplant_rejection", "immunosuppression",
            "chronic_fatigue_syndrome", "fibromyalgia", "mast_cell_activation_syndrome"
        ],
        "infectious": [
            "bacterial_infection", "viral_infection", "fungal_infection", "parasitic_infection",
            "sepsis", "meningitis", "encephalitis", "pneumonia", "tuberculosis", "hiv_aids",
            "hepatitis", "influenza", "covid_19", "mononucleosis", "cytomegalovirus",
            "herpes_simplex", "herpes_zoster", "varicella", "measles", "mumps", "rubella",
            "pertussis", "diphtheria", "tetanus", "malaria", "lyme_disease", "rocky_mountain_spotted_fever"
        ],
        "psychiatric": [
            "depression", "anxiety", "bipolar_disorder", "schizophrenia", "obsessive_compulsive_disorder",
            "post_traumatic_stress_disorder", "attention_deficit_hyperactivity_disorder",
            "autism_spectrum_disorder", "eating_disorder", "anorexia_nervosa", "bulimia_nervosa",
            "binge_eating_disorder", "substance_abuse", "alcoholism", "drug_addiction",
            "personality_disorder", "borderline_personality_disorder", "antisocial_personality_disorder",
            "panic_disorder", "social_anxiety_disorder", "generalized_anxiety_disorder",
            "seasonal_affective_disorder", "dissociative_disorder", "somatic_symptom_disorder"
        ],
        "reproductive": [
            "endometriosis", "polycystic_ovary_syndrome", "uterine_fibroids", "ovarian_cysts",
            "cervical_cancer", "ovarian_cancer", "uterine_cancer", "breast_cancer",
            "prostate_cancer", "testicular_cancer", "erectile_dysfunction", "infertility",
            "menstrual_disorders", "dysmenorrhea", "amenorrhea", "menorrhagia",
            "premenstrual_syndrome", "menopause", "andropause", "sexually_transmitted_infection",
            "pelvic_inflammatory_disease", "benign_prostatic_hyperplasia", "prostatitis"
        ],
        "pediatric": [
            "febrile_seizure", "croup", "bronchiolitis", "hand_foot_mouth_disease",
            "chickenpox", "measles", "mumps", "rubella", "whooping_cough", "rotavirus",
            "respiratory_syncytial_virus", "ear_infection", "strep_throat", "impetigo",
            "ringworm", "head_lice", "scabies", "diaper_rash", "colic", "reflux",
            "failure_to_thrive", "developmental_delay", "autism_spectrum_disorder",
            "attention_deficit_hyperactivity_disorder", "learning_disability"
        ],
        "geriatric": [
            "dementia", "alzheimers_disease", "parkinsons_disease", "osteoporosis",
            "arthritis", "cataracts", "glaucoma", "macular_degeneration", "hearing_loss",
            "urinary_incontinence", "constipation", "pressure_ulcers", "falls",
            "delirium", "depression", "anxiety", "sleep_disorders", "malnutrition",
            "dehydration", "polypharmacy", "frailty", "sarcopenia"
        ],
        "emergency": [
            "cardiac_arrest", "stroke", "heart_attack", "severe_bleeding", "shock",
            "anaphylaxis", "severe_allergic_reaction", "poisoning", "overdose",
            "severe_burns", "head_injury", "spinal_cord_injury", "multiple_trauma",
            "respiratory_distress", "severe_asthma_attack", "pulmonary_embolism",
            "aortic_dissection", "ruptured_aneurysm", "acute_abdomen", "appendicitis",
            "ectopic_pregnancy", "severe_infection", "sepsis", "meningitis",
            "heat_stroke", "hypothermia", "frostbite", "near_drowning"
        ]
    }
    
    # Severity levels
    SEVERITY_LEVELS = ["mild", "moderate", "severe", "critical"]
    
    # Urgency levels
    URGENCY_LEVELS = ["low", "normal", "high", "emergency"]
    
    # Confidence thresholds
    CONFIDENCE_THRESHOLDS = {
        "high": 0.8,
        "medium": 0.6,
        "low": 0.4
    }
    
    # Model performance expectations
    PERFORMANCE_EXPECTATIONS = {
        "biogpt": {
            "accuracy": 0.89,
            "speed_ms": 3000,
            "medical_specialized": True,
            "strengths": ["biomedical_text", "clinical_terminology", "medical_literature"],
            "limitations": ["vision_analysis", "real_time_processing"]
        },
        "pubmedgpt": {
            "accuracy": 0.91,
            "speed_ms": 3500,
            "medical_specialized": True,
            "strengths": ["medical_research", "evidence_based", "clinical_guidelines"],
            "limitations": ["vision_analysis", "real_time_processing"]
        }
    }
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        if model_name.lower() == "biogpt":
            return cls.BIOGPT_CONFIG
        elif model_name.lower() == "pubmedgpt":
            return cls.PUBMEDGPT_CONFIG
        else:
            raise ValueError(f"Unknown model: {model_name}")
    
    @classmethod
    def get_medical_conditions(cls, category: str = None) -> Dict[str, Any]:
        """Get medical conditions by category or all categories."""
        if category:
            return cls.MEDICAL_CONDITIONS.get(category.lower(), [])
        return cls.MEDICAL_CONDITIONS
    
    @classmethod
    def get_performance_expectations(cls, model_name: str) -> Dict[str, Any]:
        """Get performance expectations for a model."""
        return cls.PERFORMANCE_EXPECTATIONS.get(model_name.lower(), {}) 