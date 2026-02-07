"""
Clinical Reports Service
Service layer for clinical reports management with versioning and workflow.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import IntegrityError

from apps.medical_records.models.clinical_reports import (
    ClinicalReportDB, ReportVersionDB, ReportTemplateDB, 
    ReportCategoryDB, ReportAuditLogDB,
    ReportType, ReportStatus, ReportPriority, ReportCategory, ReportTemplate
)
from apps.medical_records.schemas.clinical_reports import (
    ClinicalReportCreate, ClinicalReportUpdate, ClinicalReportResponse,
    ClinicalReportListResponse, ReportVersionResponse, ReportVersionListResponse,
    ReportTemplateCreate, ReportTemplateUpdate, ReportTemplateResponse,
    ReportTemplateListResponse, ReportCategoryCreate, ReportCategoryUpdate,
    ReportCategoryResponse, ReportCategoryListResponse, ReportAuditLogResponse,
    ReportAuditLogListResponse, ReportSearchRequest, ReportStatisticsResponse
)
from apps.medical_records.services.service_integration import service_integration
from common.database.connection import get_session
from common.utils.logging import get_logger

logger = get_logger(__name__)


class ClinicalReportsService:
    """Service for clinical reports management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_report(
        self, 
        db: Session, 
        report_data: ClinicalReportCreate, 
        author_id: UUID
    ) -> ClinicalReportResponse:
        """Create a new clinical report."""
        try:
            # Create new report
            report = ClinicalReportDB(
                patient_id=report_data.patient_id,
                author_id=author_id,
                title=report_data.title,
                report_type=report_data.report_type,
                category=report_data.category,
                template=report_data.template,
                content=report_data.content,
                summary=report_data.summary,
                keywords=report_data.keywords,
                status=report_data.status,
                priority=report_data.priority,
                is_confidential=report_data.is_confidential,
                requires_review=report_data.requires_review,
                parent_report_id=report_data.parent_report_id,
                effective_date=report_data.effective_date,
                expiry_date=report_data.expiry_date,
                external_id=report_data.external_id,
                fhir_resource_id=report_data.fhir_resource_id,
                source_system=report_data.source_system,
                tags=report_data.tags,
                attachments=report_data.attachments,
                report_metadata=report_data.report_metadata
            )
            
            # Handle versioning if parent report exists
            if report_data.parent_report_id:
                parent_report = db.query(ClinicalReportDB).filter(
                    ClinicalReportDB.id == report_data.parent_report_id
                ).first()
                if parent_report:
                    # Mark parent as not latest version
                    parent_report.is_latest_version = False
                    report.version = parent_report.version + 1
                else:
                    raise ValueError("Parent report not found")
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            # Create initial version record
            version = ReportVersionDB(
                report_id=report.id,
                version_number=report.version,
                content=report.content,
                summary=report.summary,
                author_id=author_id
            )
            db.add(version)
            
            # Create audit log
            audit_log = ReportAuditLogDB(
                report_id=report.id,
                user_id=author_id,
                action="CREATE",
                new_values={
                    "title": report.title,
                    "report_type": report.report_type.value,
                    "status": report.status.value
                }
            )
            db.add(audit_log)
            
            db.commit()
            
            # Return response with version count
            response_data = self._prepare_report_response(report, db)
            return ClinicalReportResponse(**response_data)
            
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error creating report: {e}")
            raise ValueError("Report creation failed due to constraint violation")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating report: {e}")
            raise
    
    def get_report(
        self, 
        db: Session, 
        report_id: UUID, 
        user_id: UUID
    ) -> ClinicalReportResponse:
        """Get a clinical report by ID."""
        try:
            # User access is validated at the API layer
            
            report = db.query(ClinicalReportDB).filter(
                ClinicalReportDB.id == report_id
            ).first()
            
            if not report:
                raise ValueError("Report not found")
            
            # Create audit log for view
            audit_log = ReportAuditLogDB(
                report_id=report_id,
                user_id=user_id,
                action="VIEW"
            )
            db.add(audit_log)
            db.commit()
            
            response_data = self._prepare_report_response(report, db)
            return ClinicalReportResponse(**response_data)
            
        except Exception as e:
            self.logger.error(f"Error getting report: {e}")
            raise
    
    def update_report(
        self, 
        db: Session, 
        report_id: UUID, 
        report_data: ClinicalReportUpdate, 
        user_id: UUID
    ) -> ClinicalReportResponse:
        """Update a clinical report."""
        try:
            # Validate user access
            # User access is validated at the API layer
            
            report = db.query(ClinicalReportDB).filter(
                ClinicalReportDB.id == report_id
            ).first()
            
            if not report:
                raise ValueError("Report not found")
            
            # Store old values for audit
            old_values = {
                "title": report.title,
                "content": report.content,
                "status": report.status.value,
                "priority": report.priority.value
            }
            
            # Update fields
            update_data = report_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(report, field, value)
            
            report.modified_date = datetime.utcnow()
            
            # Create new version if content changed
            if 'content' in update_data:
                report.version += 1
                report.is_latest_version = True
                
                # Mark previous version as not latest
                db.query(ClinicalReportDB).filter(
                    ClinicalReportDB.parent_report_id == report_id
                ).update({"is_latest_version": False})
                
                # Create new version record
                version = ReportVersionDB(
                    report_id=report.id,
                    version_number=report.version,
                    content=report.content,
                    summary=report.summary,
                    author_id=user_id,
                    changes_summary=f"Updated by user {user_id}"
                )
                db.add(version)
            
            # Create audit log
            audit_log = ReportAuditLogDB(
                report_id=report_id,
                user_id=user_id,
                action="UPDATE",
                old_values=old_values,
                new_values={
                    "title": report.title,
                    "content": report.content,
                    "status": report.status.value,
                    "priority": report.priority.value
                },
                changes_summary=f"Updated fields: {', '.join(update_data.keys())}"
            )
            db.add(audit_log)
            
            db.commit()
            db.refresh(report)
            
            response_data = self._prepare_report_response(report, db)
            return ClinicalReportResponse(**response_data)
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating report: {e}")
            raise
    
    def delete_report(
        self, 
        db: Session, 
        report_id: UUID, 
        user_id: UUID
    ) -> bool:
        """Delete a clinical report."""
        try:
            # Validate user access
            # User access is validated at the API layer
            
            report = db.query(ClinicalReportDB).filter(
                ClinicalReportDB.id == report_id
            ).first()
            
            if not report:
                raise ValueError("Report not found")
            
            # Create audit log before deletion
            audit_log = ReportAuditLogDB(
                report_id=report_id,
                user_id=user_id,
                action="DELETE",
                old_values={
                    "title": report.title,
                    "report_type": report.report_type.value,
                    "status": report.status.value
                }
            )
            db.add(audit_log)
            
            # Soft delete by changing status
            report.status = ReportStatus.ARCHIVED
            report.modified_date = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error deleting report: {e}")
            raise
    
    def search_reports(
        self, 
        db: Session, 
        search_request: ReportSearchRequest, 
        user_id: UUID
    ) -> ClinicalReportListResponse:
        """Search clinical reports with filters."""
        try:
            # Validate user access
            # # User access is validated at the API layer
            
            query = db.query(ClinicalReportDB)
            
            # Apply filters
            if search_request.patient_id:
                query = query.filter(ClinicalReportDB.patient_id == search_request.patient_id)
            
            if search_request.report_type:
                query = query.filter(ClinicalReportDB.report_type == search_request.report_type)
            
            if search_request.category:
                query = query.filter(ClinicalReportDB.category == search_request.category)
            
            if search_request.status:
                query = query.filter(ClinicalReportDB.status == search_request.status)
            
            if search_request.priority:
                query = query.filter(ClinicalReportDB.priority == search_request.priority)
            
            if search_request.author_id:
                query = query.filter(ClinicalReportDB.author_id == search_request.author_id)
            
            if search_request.is_confidential is not None:
                query = query.filter(ClinicalReportDB.is_confidential == search_request.is_confidential)
            
            if search_request.requires_review is not None:
                query = query.filter(ClinicalReportDB.requires_review == search_request.requires_review)
            
            if search_request.date_from:
                query = query.filter(ClinicalReportDB.created_date >= search_request.date_from)
            
            if search_request.date_to:
                query = query.filter(ClinicalReportDB.created_date <= search_request.date_to)
            
            if search_request.tags:
                for tag in search_request.tags:
                    query = query.filter(ClinicalReportDB.tags.contains([tag]))
            
            # Apply search query
            if search_request.query:
                search_term = f"%{search_request.query}%"
                query = query.filter(
                    or_(
                        ClinicalReportDB.title.ilike(search_term),
                        ClinicalReportDB.content.ilike(search_term),
                        ClinicalReportDB.summary.ilike(search_term)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if search_request.sort_by == "created_date":
                sort_field = ClinicalReportDB.created_date
            elif search_request.sort_by == "modified_date":
                sort_field = ClinicalReportDB.modified_date
            elif search_request.sort_by == "title":
                sort_field = ClinicalReportDB.title
            elif search_request.sort_by == "priority":
                sort_field = ClinicalReportDB.priority
            else:
                sort_field = ClinicalReportDB.created_date
            
            if search_request.sort_order == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))
            
            # Apply pagination
            offset = (search_request.page - 1) * search_request.size
            reports = query.offset(offset).limit(search_request.size).all()
            
            # Prepare response
            report_responses = []
            for report in reports:
                response_data = self._prepare_report_response(report, db)
                report_responses.append(ClinicalReportResponse(**response_data))
            
            pages = (total + search_request.size - 1) // search_request.size
            
            return ClinicalReportListResponse(
                reports=report_responses,
                total=total,
                page=search_request.page,
                size=search_request.size,
                pages=pages
            )
            
        except Exception as e:
            self.logger.error(f"Error searching reports: {e}")
            raise
    
    def get_report_versions(
        self, 
        db: Session, 
        report_id: UUID, 
        user_id: UUID
    ) -> ReportVersionListResponse:
        """Get all versions of a report."""
        try:
            # Validate user access
            # User access is validated at the API layer
            
            # Get main report
            report = db.query(ClinicalReportDB).filter(
                ClinicalReportDB.id == report_id
            ).first()
            
            if not report:
                raise ValueError("Report not found")
            
            # Get all versions including the main report
            versions = db.query(ReportVersionDB).filter(
                ReportVersionDB.report_id == report_id
            ).order_by(desc(ReportVersionDB.version_number)).all()
            
            # Add current version if not in versions table
            version_responses = []
            current_version_found = False
            
            for version in versions:
                if version.version_number == report.version:
                    current_version_found = True
                version_responses.append(ReportVersionResponse(
                    id=version.id,
                    report_id=version.report_id,
                    version_number=version.version_number,
                    content=version.content,
                    summary=version.summary,
                    changes_summary=version.changes_summary,
                    author_id=version.author_id,
                    created_date=version.created_date,
                    version_metadata=version.version_metadata,
                    created_at=version.created_at,
                    updated_at=version.updated_at
                ))
            
            # Add current version if not found
            if not current_version_found:
                version_responses.insert(0, ReportVersionResponse(
                    id=uuid4(),
                    report_id=report.id,
                    version_number=report.version,
                    content=report.content,
                    summary=report.summary,
                    changes_summary="Current version",
                    author_id=report.author_id,
                    created_date=report.modified_date,
                    version_metadata=None,
                    created_at=report.created_at,
                    updated_at=report.updated_at
                ))
            
            return ReportVersionListResponse(
                versions=version_responses,
                total=len(version_responses),
                current_version=report.version
            )
            
        except Exception as e:
            self.logger.error(f"Error getting report versions: {e}")
            raise
    
    def create_report_template(
        self, 
        db: Session, 
        template_data: ReportTemplateCreate, 
        author_id: UUID
    ) -> ReportTemplateResponse:
        """Create a new report template."""
        try:
            template = ReportTemplateDB(
                name=template_data.name,
                version=template_data.version,
                template_type=template_data.template_type,
                category=template_data.category,
                template_content=template_data.template_content,
                template_schema=template_data.template_schema,
                default_values=template_data.default_values,
                description=template_data.description,
                author_id=author_id,
                is_system_template=template_data.is_system_template
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            return ReportTemplateResponse(
                id=template.id,
                name=template.name,
                version=template.version,
                template_type=template.template_type,
                category=template.category,
                template_content=template.template_content,
                template_schema=template.template_schema,
                default_values=template.default_values,
                description=template.description,
                author_id=template.author_id,
                is_active=template.is_active,
                is_system_template=template.is_system_template,
                usage_count=template.usage_count,
                last_used_date=template.last_used_date,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error creating template: {e}")
            raise ValueError("Template creation failed due to constraint violation")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating template: {e}")
            raise
    
    def get_report_templates(
        self, 
        db: Session, 
        user_id: UUID,
        category: Optional[ReportCategory] = None,
        template_type: Optional[ReportTemplate] = None,
        is_active: Optional[bool] = None
    ) -> ReportTemplateListResponse:
        """Get report templates with filters."""
        try:
            query = db.query(ReportTemplateDB)
            
            if category:
                query = query.filter(ReportTemplateDB.category == category)
            
            if template_type:
                query = query.filter(ReportTemplateDB.template_type == template_type)
            
            if is_active is not None:
                query = query.filter(ReportTemplateDB.is_active == is_active)
            
            templates = query.order_by(asc(ReportTemplateDB.name)).all()
            
            template_responses = []
            for template in templates:
                template_responses.append(ReportTemplateResponse(
                    id=template.id,
                    name=template.name,
                    version=template.version,
                    template_type=template.template_type,
                    category=template.category,
                    template_content=template.template_content,
                    template_schema=template.template_schema,
                    default_values=template.default_values,
                    description=template.description,
                    author_id=template.author_id,
                    is_active=template.is_active,
                    is_system_template=template.is_system_template,
                    usage_count=template.usage_count,
                    last_used_date=template.last_used_date,
                    created_at=template.created_at,
                    updated_at=template.updated_at
                ))
            
            return ReportTemplateListResponse(
                templates=template_responses,
                total=len(template_responses),
                page=1,
                size=len(template_responses),
                pages=1
            )
            
        except Exception as e:
            self.logger.error(f"Error getting templates: {e}")
            raise
    
    def create_report_category(
        self, 
        db: Session, 
        category_data: ReportCategoryCreate, 
        user_id: UUID
    ) -> ReportCategoryResponse:
        """Create a new report category."""
        try:
            category = ReportCategoryDB(
                name=category_data.name,
                description=category_data.description,
                parent_id=category_data.parent_id,
                color_code=category_data.color_code,
                icon_name=category_data.icon_name,
                sort_order=category_data.sort_order
            )
            
            db.add(category)
            db.commit()
            db.refresh(category)
            
            return self._prepare_category_response(category)
            
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error creating category: {e}")
            raise ValueError("Category creation failed due to constraint violation")
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating category: {e}")
            raise
    
    def get_report_categories(
        self, 
        db: Session, 
        user_id: UUID,
        include_inactive: bool = False
    ) -> ReportCategoryListResponse:
        """Get report categories."""
        try:
            query = db.query(ReportCategoryDB)
            
            if not include_inactive:
                query = query.filter(ReportCategoryDB.is_active == True)
            
            categories = query.order_by(asc(ReportCategoryDB.sort_order)).all()
            
            category_responses = []
            for category in categories:
                category_responses.append(self._prepare_category_response(category))
            
            return ReportCategoryListResponse(
                categories=category_responses,
                total=len(category_responses)
            )
            
        except Exception as e:
            self.logger.error(f"Error getting categories: {e}")
            raise
    
    def get_report_audit_logs(
        self, 
        db: Session, 
        report_id: UUID, 
        user_id: UUID,
        page: int = 1,
        size: int = 20
    ) -> ReportAuditLogListResponse:
        """Get audit logs for a report."""
        try:
            # Validate user access
            # User access is validated at the API layer
            
            query = db.query(ReportAuditLogDB).filter(
                ReportAuditLogDB.report_id == report_id
            )
            
            total = query.count()
            
            audit_logs = query.order_by(desc(ReportAuditLogDB.timestamp)).offset(
                (page - 1) * size
            ).limit(size).all()
            
            audit_log_responses = []
            for log in audit_logs:
                audit_log_responses.append(ReportAuditLogResponse(
                    id=log.id,
                    report_id=log.report_id,
                    user_id=log.user_id,
                    action=log.action,
                    timestamp=log.timestamp,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    old_values=log.old_values,
                    new_values=log.new_values,
                    changes_summary=log.changes_summary,
                    session_id=log.session_id,
                    request_id=log.request_id,
                    created_at=log.created_at
                ))
            
            pages = (total + size - 1) // size
            
            return ReportAuditLogListResponse(
                audit_logs=audit_log_responses,
                total=total,
                page=page,
                size=size,
                pages=pages
            )
            
        except Exception as e:
            self.logger.error(f"Error getting audit logs: {e}")
            raise
    
    def get_report_statistics(
        self, 
        db: Session, 
        user_id: UUID,
        patient_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> ReportStatisticsResponse:
        """Get report statistics."""
        try:
            # User access is validated at the API layer
            
            query = db.query(ClinicalReportDB)
            
            if patient_id:
                query = query.filter(ClinicalReportDB.patient_id == patient_id)
            
            if date_from:
                query = query.filter(ClinicalReportDB.created_date >= date_from)
            
            if date_to:
                query = query.filter(ClinicalReportDB.created_date <= date_to)
            
            # Total reports
            total_reports = query.count()
            
            # Reports by type
            reports_by_type = {}
            type_counts = db.query(
                ClinicalReportDB.report_type,
                func.count(ClinicalReportDB.id)
            ).group_by(ClinicalReportDB.report_type).all()
            
            for report_type, count in type_counts:
                reports_by_type[report_type.value] = count
            
            # Reports by status
            reports_by_status = {}
            status_counts = db.query(
                ClinicalReportDB.status,
                func.count(ClinicalReportDB.id)
            ).group_by(ClinicalReportDB.status).all()
            
            for status, count in status_counts:
                reports_by_status[status.value] = count
            
            # Reports by category
            reports_by_category = {}
            category_counts = db.query(
                ClinicalReportDB.category,
                func.count(ClinicalReportDB.id)
            ).group_by(ClinicalReportDB.category).all()
            
            for category, count in category_counts:
                reports_by_category[category.value] = count
            
            # Reports by priority
            reports_by_priority = {}
            priority_counts = db.query(
                ClinicalReportDB.priority,
                func.count(ClinicalReportDB.id)
            ).group_by(ClinicalReportDB.priority).all()
            
            for priority, count in priority_counts:
                reports_by_priority[priority.value] = count
            
            # Reports by month
            reports_by_month = {}
            month_counts = db.query(
                func.date_trunc('month', ClinicalReportDB.created_date),
                func.count(ClinicalReportDB.id)
            ).group_by(
                func.date_trunc('month', ClinicalReportDB.created_date)
            ).order_by(
                func.date_trunc('month', ClinicalReportDB.created_date)
            ).all()
            
            for month, count in month_counts:
                reports_by_month[month.strftime('%Y-%m')] = count
            
            # Average versions per report
            version_counts = db.query(
                ClinicalReportDB.id,
                func.count(ReportVersionDB.id)
            ).outerjoin(ReportVersionDB).group_by(ClinicalReportDB.id).all()
            
            if version_counts:
                total_versions = sum(count for _, count in version_counts)
                average_versions = total_versions / len(version_counts)
            else:
                average_versions = 0.0
            
            # Reports requiring review
            reports_requiring_review = query.filter(
                ClinicalReportDB.requires_review == True
            ).count()
            
            # Confidential reports
            confidential_reports = query.filter(
                ClinicalReportDB.is_confidential == True
            ).count()
            
            return ReportStatisticsResponse(
                total_reports=total_reports,
                reports_by_type=reports_by_type,
                reports_by_status=reports_by_status,
                reports_by_category=reports_by_category,
                reports_by_priority=reports_by_priority,
                reports_by_month=reports_by_month,
                average_versions_per_report=average_versions,
                reports_requiring_review=reports_requiring_review,
                confidential_reports=confidential_reports
            )
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            raise
    
    def _prepare_report_response(self, report: ClinicalReportDB, db: Session) -> Dict[str, Any]:
        """Prepare report response data."""
        # Get version count
        version_count = db.query(ReportVersionDB).filter(
            ReportVersionDB.report_id == report.id
        ).count()
        
        return {
            "id": report.id,
            "patient_id": report.patient_id,
            "author_id": report.author_id,
            "reviewer_id": report.reviewer_id,
            "title": report.title,
            "report_type": report.report_type,
            "category": report.category,
            "template": report.template,
            "content": report.content,
            "summary": report.summary,
            "keywords": report.keywords,
            "status": report.status,
            "priority": report.priority,
            "is_confidential": report.is_confidential,
            "requires_review": report.requires_review,
            "version": report.version,
            "parent_report_id": report.parent_report_id,
            "is_latest_version": report.is_latest_version,
            "version_count": version_count,
            "created_date": report.created_date,
            "modified_date": report.modified_date,
            "reviewed_date": report.reviewed_date,
            "published_date": report.published_date,
            "effective_date": report.effective_date,
            "expiry_date": report.expiry_date,
            "external_id": report.external_id,
            "fhir_resource_id": report.fhir_resource_id,
            "source_system": report.source_system,
            "tags": report.tags,
            "attachments": report.attachments,
            "report_metadata": report.report_metadata,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
    
    def _prepare_category_response(self, category: ReportCategoryDB) -> ReportCategoryResponse:
        """Prepare category response data."""
        return ReportCategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            color_code=category.color_code,
            icon_name=category.icon_name,
            sort_order=category.sort_order,
            is_active=category.is_active,
            report_count=category.report_count,
            subcategories=[],  # Will be populated if needed
            created_at=category.created_at,
            updated_at=category.updated_at
        )


# Global service instance
clinical_reports_service = ClinicalReportsService() 