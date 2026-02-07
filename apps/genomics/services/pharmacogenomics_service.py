"""
Pharmacogenomics service for Personal Health Assistant.

This service handles pharmacogenomic analysis including:
- Drug-gene interaction analysis
- Metabolizer status assessment
- Drug response predictions
- Medication recommendations
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.genomic_data import (
    PharmacogenomicProfile, PharmacogenomicProfileCreate, PharmacogenomicProfileResponse
)
from common.exceptions import NotFoundError, ValidationError


class PharmacogenomicsService:
    """Service for managing pharmacogenomic analysis."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_profile(
        self, 
        profile: PharmacogenomicProfileCreate, 
        user_id: uuid.UUID
    ) -> PharmacogenomicProfileResponse:
        """Create new pharmacogenomic profile."""
        try:
            pharmacogenomic_profile = PharmacogenomicProfile(
                user_id=user_id,
                profile_name=profile.profile_name,
                test_date=profile.test_date,
                lab_name=profile.lab_name,
                test_method=profile.test_method,
                gene_drug_interactions=profile.gene_drug_interactions,
                metabolizer_status=profile.metabolizer_status,
                drug_risks=profile.drug_risks,
                drug_recommendations=profile.drug_recommendations,
                raw_data=profile.raw_data,
                interpretation=profile.interpretation
            )
            
            self.db.add(pharmacogenomic_profile)
            self.db.commit()
            self.db.refresh(pharmacogenomic_profile)
            
            return PharmacogenomicProfileResponse.from_orm(pharmacogenomic_profile)
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to create pharmacogenomic profile: {str(e)}")
    
    async def list_profiles(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[PharmacogenomicProfileResponse]:
        """List pharmacogenomic profiles for user."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).offset(skip).limit(limit).all()
            
            return [PharmacogenomicProfileResponse.from_orm(profile) for profile in profiles]
        except Exception as e:
            raise ValidationError(f"Failed to list pharmacogenomic profiles: {str(e)}")
    
    async def get_profile(
        self, 
        profile_id: str, 
        user_id: uuid.UUID
    ) -> PharmacogenomicProfileResponse:
        """Get specific pharmacogenomic profile by ID."""
        try:
            profile = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.id == profile_id,
                PharmacogenomicProfile.user_id == user_id
            ).first()
            
            if not profile:
                raise NotFoundError("Pharmacogenomic profile not found")
            
            return PharmacogenomicProfileResponse.from_orm(profile)
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to get pharmacogenomic profile: {str(e)}")
    
    async def update_profile(
        self,
        profile_id: str,
        profile: PharmacogenomicProfileCreate,
        user_id: uuid.UUID
    ) -> PharmacogenomicProfileResponse:
        """Update pharmacogenomic profile."""
        try:
            existing_profile = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.id == profile_id,
                PharmacogenomicProfile.user_id == user_id
            ).first()
            
            if not existing_profile:
                raise NotFoundError("Pharmacogenomic profile not found")
            
            # Update fields
            for field, value in profile.dict(exclude={'user_id'}).items():
                setattr(existing_profile, field, value)
            
            existing_profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_profile)
            
            return PharmacogenomicProfileResponse.from_orm(existing_profile)
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to update pharmacogenomic profile: {str(e)}")
    
    async def delete_profile(
        self, 
        profile_id: str, 
        user_id: uuid.UUID
    ) -> None:
        """Delete pharmacogenomic profile."""
        try:
            profile = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.id == profile_id,
                PharmacogenomicProfile.user_id == user_id
            ).first()
            
            if not profile:
                raise NotFoundError("Pharmacogenomic profile not found")
            
            self.db.delete(profile)
            self.db.commit()
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to delete pharmacogenomic profile: {str(e)}")
    
    async def get_drug_interactions(
        self,
        user_id: uuid.UUID,
        drug_name: Optional[str] = None,
        gene_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get drug-gene interactions for the user."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            interactions = []
            for profile in profiles:
                for interaction in profile.gene_drug_interactions:
                    if drug_name and drug_name.lower() not in interaction.get('drug_name', '').lower():
                        continue
                    if gene_name and gene_name.lower() not in interaction.get('gene_name', '').lower():
                        continue
                    
                    interactions.append({
                        "profile_id": str(profile.id),
                        "profile_name": profile.profile_name,
                        "test_date": profile.test_date,
                        **interaction
                    })
            
            return interactions[skip:skip + limit]
        except Exception as e:
            raise ValidationError(f"Failed to get drug interactions: {str(e)}")
    
    async def get_metabolizer_status(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get metabolizer status for the user."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return {"message": "No pharmacogenomic profiles found"}
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            return {
                "profile_id": str(latest_profile.id),
                "profile_name": latest_profile.profile_name,
                "test_date": latest_profile.test_date,
                "metabolizer_status": latest_profile.metabolizer_status
            }
        except Exception as e:
            raise ValidationError(f"Failed to get metabolizer status: {str(e)}")
    
    async def predict_drug_response(
        self,
        user_id: uuid.UUID,
        drug_name: str,
        dosage: Optional[float] = None
    ) -> Dict[str, Any]:
        """Predict drug response based on pharmacogenomic profile."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                raise ValidationError("No pharmacogenomic profiles found")
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            # Find drug interaction
            drug_interaction = None
            for interaction in latest_profile.gene_drug_interactions:
                if drug_name.lower() in interaction.get('drug_name', '').lower():
                    drug_interaction = interaction
                    break
            
            if not drug_interaction:
                return {
                    "drug_name": drug_name,
                    "prediction": "No pharmacogenomic data available",
                    "confidence": "low",
                    "recommendation": "Standard dosing recommended"
                }
            
            # Simulate prediction based on interaction data
            prediction = self._simulate_drug_response(drug_interaction, dosage)
            
            return {
                "drug_name": drug_name,
                "profile_id": str(latest_profile.id),
                "interaction_data": drug_interaction,
                "prediction": prediction,
                "confidence": drug_interaction.get('confidence', 'medium'),
                "recommendation": drug_interaction.get('recommendation', 'Consult healthcare provider')
            }
        except Exception as e:
            raise ValidationError(f"Failed to predict drug response: {str(e)}")
    
    async def get_medication_recommendations(
        self,
        user_id: uuid.UUID,
        condition: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get personalized medication recommendations."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return []
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            recommendations = []
            for rec in latest_profile.drug_recommendations:
                if condition and condition.lower() not in rec.get('condition', '').lower():
                    continue
                
                recommendations.append({
                    "profile_id": str(latest_profile.id),
                    "profile_name": latest_profile.profile_name,
                    **rec
                })
            
            return recommendations
        except Exception as e:
            raise ValidationError(f"Failed to get medication recommendations: {str(e)}")
    
    async def get_drug_risks(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get drug-related risks for the user."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return []
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            risks = []
            for risk in latest_profile.drug_risks:
                risks.append({
                    "profile_id": str(latest_profile.id),
                    "profile_name": latest_profile.profile_name,
                    **risk
                })
            
            return risks
        except Exception as e:
            raise ValidationError(f"Failed to get drug risks: {str(e)}")
    
    async def analyze_medication(
        self,
        user_id: uuid.UUID,
        medication_list: List[str]
    ) -> Dict[str, Any]:
        """Analyze medication list for pharmacogenomic interactions."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return {
                    "message": "No pharmacogenomic profiles found",
                    "medications": medication_list,
                    "interactions": [],
                    "risks": [],
                    "recommendations": []
                }
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            interactions = []
            risks = []
            recommendations = []
            
            for medication in medication_list:
                # Check for interactions
                for interaction in latest_profile.gene_drug_interactions:
                    if medication.lower() in interaction.get('drug_name', '').lower():
                        interactions.append({
                            "medication": medication,
                            **interaction
                        })
                
                # Check for risks
                for risk in latest_profile.drug_risks:
                    if medication.lower() in risk.get('drug_name', '').lower():
                        risks.append({
                            "medication": medication,
                            **risk
                        })
            
            return {
                "profile_id": str(latest_profile.id),
                "profile_name": latest_profile.profile_name,
                "medications": medication_list,
                "interactions": interactions,
                "risks": risks,
                "recommendations": latest_profile.drug_recommendations
            }
        except Exception as e:
            raise ValidationError(f"Failed to analyze medication: {str(e)}")
    
    async def get_pharmacogenomic_genes(
        self, 
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get pharmacogenomic genes for the user."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return []
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            genes = set()
            for interaction in latest_profile.gene_drug_interactions:
                gene_name = interaction.get('gene_name')
                if gene_name:
                    genes.add(gene_name)
            
            return [
                {
                    "gene_name": gene,
                    "profile_id": str(latest_profile.id),
                    "profile_name": latest_profile.profile_name
                }
                for gene in sorted(genes)
            ]
        except Exception as e:
            raise ValidationError(f"Failed to get pharmacogenomic genes: {str(e)}")
    
    async def get_pharmacogenomic_drugs(
        self,
        user_id: uuid.UUID,
        gene_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get drugs with pharmacogenomic implications."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return []
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            drugs = []
            for interaction in latest_profile.gene_drug_interactions:
                if gene_name and gene_name.lower() not in interaction.get('gene_name', '').lower():
                    continue
                
                drugs.append({
                    "drug_name": interaction.get('drug_name'),
                    "gene_name": interaction.get('gene_name'),
                    "interaction_type": interaction.get('interaction_type'),
                    "severity": interaction.get('severity'),
                    "profile_id": str(latest_profile.id),
                    "profile_name": latest_profile.profile_name
                })
            
            return drugs
        except Exception as e:
            raise ValidationError(f"Failed to get pharmacogenomic drugs: {str(e)}")
    
    async def interpret_pharmacogenomic_data(
        self,
        profile_id: str,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Interpret pharmacogenomic data and generate recommendations."""
        try:
            profile = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.id == profile_id,
                PharmacogenomicProfile.user_id == user_id
            ).first()
            
            if not profile:
                raise NotFoundError("Pharmacogenomic profile not found")
            
            # Generate interpretation
            interpretation = {
                "profile_id": str(profile.id),
                "profile_name": profile.profile_name,
                "test_date": profile.test_date,
                "summary": self._generate_interpretation_summary(profile),
                "key_findings": self._extract_key_findings(profile),
                "recommendations": profile.drug_recommendations,
                "risks": profile.drug_risks,
                "metabolizer_status": profile.metabolizer_status
            }
            
            # Update profile with interpretation
            profile.interpretation = interpretation.get('summary')
            profile.is_interpreted = True
            profile.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return interpretation
        except NotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationError(f"Failed to interpret pharmacogenomic data: {str(e)}")
    
    async def get_pharmacogenomic_statistics(
        self, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get pharmacogenomic statistics for the user."""
        try:
            profiles = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.user_id == user_id
            ).all()
            
            if not profiles:
                return {"message": "No pharmacogenomic profiles found"}
            
            # Use the most recent profile
            latest_profile = max(profiles, key=lambda p: p.test_date)
            
            total_interactions = len(latest_profile.gene_drug_interactions)
            high_risk_interactions = len([
                i for i in latest_profile.gene_drug_interactions 
                if i.get('severity') == 'high'
            ])
            
            return {
                "total_profiles": len(profiles),
                "latest_profile_date": latest_profile.test_date,
                "total_drug_interactions": total_interactions,
                "high_risk_interactions": high_risk_interactions,
                "metabolizer_status": latest_profile.metabolizer_status,
                "is_interpreted": latest_profile.is_interpreted
            }
        except Exception as e:
            raise ValidationError(f"Failed to get pharmacogenomic statistics: {str(e)}")
    
    async def export_pharmacogenomic_report(
        self,
        profile_id: str,
        user_id: uuid.UUID,
        format: str = "pdf"
    ) -> Dict[str, Any]:
        """Export pharmacogenomic report."""
        try:
            profile = self.db.query(PharmacogenomicProfile).filter(
                PharmacogenomicProfile.id == profile_id,
                PharmacogenomicProfile.user_id == user_id
            ).first()
            
            if not profile:
                raise NotFoundError("Pharmacogenomic profile not found")
            
            # Generate report content
            report_content = self._generate_report_content(profile, format)
            
            return {
                "profile_id": str(profile.id),
                "profile_name": profile.profile_name,
                "format": format,
                "content": report_content,
                "filename": f"pharmacogenomic_report_{profile.profile_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise ValidationError(f"Failed to export pharmacogenomic report: {str(e)}")
    
    def _simulate_drug_response(
        self, 
        interaction: Dict[str, Any], 
        dosage: Optional[float]
    ) -> str:
        """Simulate drug response prediction."""
        severity = interaction.get('severity', 'unknown')
        
        if severity == 'high':
            return "High risk - Avoid or use with extreme caution"
        elif severity == 'moderate':
            return "Moderate risk - Use with caution and monitoring"
        elif severity == 'low':
            return "Low risk - Standard dosing likely safe"
        else:
            return "Unknown risk - Consult healthcare provider"
    
    def _generate_interpretation_summary(self, profile: PharmacogenomicProfile) -> str:
        """Generate interpretation summary."""
        total_interactions = len(profile.gene_drug_interactions)
        high_risk = len([i for i in profile.gene_drug_interactions if i.get('severity') == 'high'])
        
        summary = f"Pharmacogenomic analysis identified {total_interactions} drug-gene interactions. "
        if high_risk > 0:
            summary += f"{high_risk} high-risk interactions require special attention. "
        
        summary += "Consult with healthcare provider for personalized medication recommendations."
        return summary
    
    def _extract_key_findings(self, profile: PharmacogenomicProfile) -> List[Dict[str, Any]]:
        """Extract key findings from profile."""
        findings = []
        
        for interaction in profile.gene_drug_interactions:
            if interaction.get('severity') in ['high', 'moderate']:
                findings.append({
                    "type": "drug_interaction",
                    "severity": interaction.get('severity'),
                    "drug": interaction.get('drug_name'),
                    "gene": interaction.get('gene_name'),
                    "description": interaction.get('description', '')
                })
        
        return findings
    
    def _generate_report_content(
        self, 
        profile: PharmacogenomicProfile, 
        format: str
    ) -> str:
        """Generate report content in specified format."""
        if format.lower() == "json":
            return {
                "profile_name": profile.profile_name,
                "test_date": profile.test_date.isoformat(),
                "lab_name": profile.lab_name,
                "gene_drug_interactions": profile.gene_drug_interactions,
                "metabolizer_status": profile.metabolizer_status,
                "drug_risks": profile.drug_risks,
                "drug_recommendations": profile.drug_recommendations
            }
        else:
            # Default to text format
            content = f"""
Pharmacogenomic Report
======================

Profile: {profile.profile_name}
Test Date: {profile.test_date}
Lab: {profile.lab_name or 'Not specified'}

Gene-Drug Interactions: {len(profile.gene_drug_interactions)}
Metabolizer Status: {profile.metabolizer_status}

Key Findings:
"""
            for interaction in profile.gene_drug_interactions:
                content += f"- {interaction.get('drug_name')} ({interaction.get('gene_name')}): {interaction.get('severity')} risk\n"
            
            return content 