#!/usr/bin/env python3
"""
Knowledge Graph Service Analytics

Advanced analytics and reporting system for the Knowledge Graph Service
and its integrations with other microservices in the Personal Health Assistant platform.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from collections import defaultdict, Counter
import statistics
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from io import BytesIO
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

# Service URLs
SERVICES = {
    "knowledge_graph": "http://knowledge-graph.localhost",
    "medical_records": "http://medical-records.localhost",
    "auth": "http://auth.localhost",
    "ai_insights": "http://ai-insights.localhost",
    "health_tracking": "http://health-tracking.localhost"
}


class KnowledgeGraphAnalytics:
    """Advanced analytics system for Knowledge Graph Service"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.analytics_data = {}
        self.performance_metrics = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def collect_comprehensive_data(self) -> Dict[str, Any]:
        """Collect comprehensive data from all services"""
        console.print("[bold cyan]📊 Collecting comprehensive analytics data...[/bold cyan]")
        
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "knowledge_graph": {},
            "service_health": {},
            "performance_metrics": {},
            "integration_metrics": {}
        }
        
        # Collect Knowledge Graph data
        try:
            # Get statistics
            response = await self.client.get(f"{SERVICES['knowledge_graph']}/api/v1/knowledge-graph/statistics")
            if response.status_code == 200:
                data["knowledge_graph"]["statistics"] = response.json()
            
            # Get entities by type
            for entity_type in ["condition", "symptom", "medication", "treatment", "procedure", "lab_test", "vital_sign", "risk_factor"]:
                response = await self.client.get(f"{SERVICES['knowledge_graph']}/api/v1/knowledge-graph/entities?entity_type={entity_type}&limit=100")
                if response.status_code == 200:
                    data["knowledge_graph"][f"{entity_type}_entities"] = response.json()
            
            # Get all entities for analysis
            response = await self.client.get(f"{SERVICES['knowledge_graph']}/api/v1/knowledge-graph/entities?limit=1000")
            if response.status_code == 200:
                data["knowledge_graph"]["all_entities"] = response.json()
                
        except Exception as e:
            console.print(f"[red]Error collecting Knowledge Graph data: {e}[/red]")
        
        # Collect service health data
        for service_name, service_url in SERVICES.items():
            try:
                response = await self.client.get(f"{service_url}/health")
                if response.status_code == 200:
                    data["service_health"][service_name] = {
                        "status": "healthy",
                        "response": response.json(),
                        "response_time": response.elapsed.total_seconds()
                    }
                else:
                    data["service_health"][service_name] = {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    }
            except Exception as e:
                data["service_health"][service_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        self.analytics_data = data
        return data
    
    def analyze_entity_distribution(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze entity distribution and patterns"""
        if not entities:
            return {}
        
        analysis = {
            "total_entities": len(entities),
            "entity_type_distribution": {},
            "confidence_distribution": {},
            "source_distribution": {},
            "evidence_level_distribution": {},
            "average_relationships": 0,
            "entity_completeness": {}
        }
        
        # Entity type distribution
        entity_types = [entity.get("entity_type", "unknown") for entity in entities]
        analysis["entity_type_distribution"] = dict(Counter(entity_types))
        
        # Confidence distribution
        confidence_levels = [entity.get("confidence", "unknown") for entity in entities]
        analysis["confidence_distribution"] = dict(Counter(confidence_levels))
        
        # Source distribution
        sources = [entity.get("source", "unknown") for entity in entities]
        analysis["source_distribution"] = dict(Counter(sources))
        
        # Evidence level distribution
        evidence_levels = [entity.get("evidence_level", "unknown") for entity in entities]
        analysis["evidence_level_distribution"] = dict(Counter(evidence_levels))
        
        # Average relationships
        relationship_counts = [entity.get("relationship_count", 0) for entity in entities]
        analysis["average_relationships"] = statistics.mean(relationship_counts) if relationship_counts else 0
        
        # Entity completeness analysis
        completeness_scores = []
        for entity in entities:
            score = 0
            required_fields = ["name", "entity_type", "description"]
            optional_fields = ["synonyms", "ontology_ids", "metadata"]
            
            for field in required_fields:
                if entity.get(field):
                    score += 1
            
            for field in optional_fields:
                if entity.get(field):
                    score += 0.5
            
            completeness_scores.append(score / (len(required_fields) + len(optional_fields) * 0.5))
        
        analysis["entity_completeness"] = {
            "average_score": statistics.mean(completeness_scores) if completeness_scores else 0,
            "min_score": min(completeness_scores) if completeness_scores else 0,
            "max_score": max(completeness_scores) if completeness_scores else 0
        }
        
        return analysis
    
    def analyze_graph_connectivity(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze graph connectivity and structure"""
        analysis = {
            "graph_density": stats.get("graph_density", 0),
            "average_degree": stats.get("average_degree", 0),
            "total_entities": stats.get("total_entities", 0),
            "total_relationships": stats.get("total_relationships", 0),
            "relationship_distribution": {},
            "connectivity_metrics": {}
        }
        
        # Relationship distribution
        relationships_by_type = stats.get("relationships_by_type", {})
        analysis["relationship_distribution"] = relationships_by_type
        
        # Connectivity metrics
        total_entities = stats.get("total_entities", 0)
        total_relationships = stats.get("total_relationships", 0)
        
        if total_entities > 0:
            analysis["connectivity_metrics"] = {
                "relationships_per_entity": total_relationships / total_entities,
                "potential_relationships": total_entities * (total_entities - 1) / 2,
                "connectivity_ratio": total_relationships / (total_entities * (total_entities - 1) / 2) if total_entities > 1 else 0
            }
        
        return analysis
    
    def analyze_service_performance(self, service_health: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze service performance and reliability"""
        analysis = {
            "total_services": len(service_health),
            "healthy_services": 0,
            "unhealthy_services": 0,
            "error_services": 0,
            "average_response_time": 0,
            "service_reliability": {},
            "performance_metrics": {}
        }
        
        response_times = []
        
        for service_name, status in service_health.items():
            if status["status"] == "healthy":
                analysis["healthy_services"] += 1
                if "response_time" in status:
                    response_times.append(status["response_time"])
            elif status["status"] == "unhealthy":
                analysis["unhealthy_services"] += 1
            else:
                analysis["error_services"] += 1
            
            analysis["service_reliability"][service_name] = status["status"]
        
        if response_times:
            analysis["average_response_time"] = statistics.mean(response_times)
            analysis["performance_metrics"] = {
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "response_time_variance": statistics.variance(response_times) if len(response_times) > 1 else 0
            }
        
        return analysis
    
    def generate_analytics_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        console.print("[bold cyan]📈 Generating analytics report...[/bold cyan]")
        
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "summary": {},
            "entity_analysis": {},
            "graph_analysis": {},
            "performance_analysis": {},
            "recommendations": [],
            "trends": {}
        }
        
        # Entity analysis
        if "all_entities" in data.get("knowledge_graph", {}):
            entities = data["knowledge_graph"]["all_entities"]
            report["entity_analysis"] = self.analyze_entity_distribution(entities)
        
        # Graph analysis
        if "statistics" in data.get("knowledge_graph", {}):
            stats = data["knowledge_graph"]["statistics"]
            report["graph_analysis"] = self.analyze_graph_connectivity(stats)
        
        # Performance analysis
        if "service_health" in data:
            report["performance_analysis"] = self.analyze_service_performance(data["service_health"])
        
        # Generate summary
        report["summary"] = {
            "total_entities": report["entity_analysis"].get("total_entities", 0),
            "total_relationships": report["graph_analysis"].get("total_relationships", 0),
            "healthy_services": report["performance_analysis"].get("healthy_services", 0),
            "total_services": report["performance_analysis"].get("total_services", 0),
            "average_response_time": report["performance_analysis"].get("average_response_time", 0)
        }
        
        # Generate recommendations
        recommendations = []
        
        # Entity completeness recommendations
        completeness_score = report["entity_analysis"].get("entity_completeness", {}).get("average_score", 0)
        if completeness_score < 0.8:
            recommendations.append("Improve entity completeness by adding missing required fields")
        
        # Graph connectivity recommendations
        connectivity_ratio = report["graph_analysis"].get("connectivity_metrics", {}).get("connectivity_ratio", 0)
        if connectivity_ratio < 0.01:
            recommendations.append("Increase graph connectivity by adding more relationships between entities")
        
        # Performance recommendations
        avg_response_time = report["performance_analysis"].get("average_response_time", 0)
        if avg_response_time > 1.0:
            recommendations.append("Optimize service response times for better user experience")
        
        report["recommendations"] = recommendations
        
        return report
    
    def create_entity_distribution_chart(self, entity_analysis: Dict[str, Any]) -> Table:
        """Create a table showing entity distribution"""
        table = Table(title="Entity Distribution Analysis")
        table.add_column("Entity Type", style="cyan", no_wrap=True)
        table.add_column("Count", style="bold", justify="right")
        table.add_column("Percentage", style="green", justify="right")
        table.add_column("Avg Relationships", style="yellow", justify="right")
        
        total_entities = entity_analysis.get("total_entities", 0)
        entity_type_dist = entity_analysis.get("entity_type_distribution", {})
        
        for entity_type, count in entity_type_dist.items():
            percentage = (count / total_entities * 100) if total_entities > 0 else 0
            table.add_row(
                entity_type.title(),
                str(count),
                f"{percentage:.1f}%",
                f"{entity_analysis.get('average_relationships', 0):.1f}"
            )
        
        return table
    
    def create_performance_table(self, performance_analysis: Dict[str, Any]) -> Table:
        """Create a table showing performance metrics"""
        table = Table(title="Service Performance Analysis")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="bold")
        table.add_column("Status", style="green")
        
        # Service health summary
        healthy = performance_analysis.get("healthy_services", 0)
        total = performance_analysis.get("total_services", 0)
        health_percentage = (healthy / total * 100) if total > 0 else 0
        
        table.add_row("Healthy Services", f"{healthy}/{total}", f"{health_percentage:.1f}%")
        table.add_row("Average Response Time", f"{performance_analysis.get('average_response_time', 0):.3f}s", "Good" if performance_analysis.get('average_response_time', 0) < 1.0 else "Needs Improvement")
        
        # Performance metrics
        perf_metrics = performance_analysis.get("performance_metrics", {})
        if perf_metrics:
            table.add_row("Min Response Time", f"{perf_metrics.get('min_response_time', 0):.3f}s", "Good")
            table.add_row("Max Response Time", f"{perf_metrics.get('max_response_time', 0):.3f}s", "Good" if perf_metrics.get('max_response_time', 0) < 2.0 else "Needs Improvement")
        
        return table
    
    def create_recommendations_table(self, recommendations: List[str]) -> Table:
        """Create a table showing recommendations"""
        table = Table(title="Analytics Recommendations")
        table.add_column("Priority", style="cyan", no_wrap=True)
        table.add_column("Recommendation", style="bold")
        table.add_column("Impact", style="green")
        
        for i, recommendation in enumerate(recommendations, 1):
            priority = "High" if "completeness" in recommendation.lower() or "connectivity" in recommendation.lower() else "Medium"
            impact = "High" if priority == "High" else "Medium"
            
            table.add_row(
                priority,
                recommendation,
                impact
            )
        
        return table
    
    async def generate_visualization_report(self, report: Dict[str, Any]) -> str:
        """Generate visualization report with charts"""
        try:
            # Create visualizations
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Entity type distribution
            entity_analysis = report.get("entity_analysis", {})
            entity_type_dist = entity_analysis.get("entity_type_distribution", {})
            if entity_type_dist:
                ax1.pie(entity_type_dist.values(), labels=entity_type_dist.keys(), autopct='%1.1f%%')
                ax1.set_title('Entity Type Distribution')
            
            # Confidence distribution
            confidence_dist = entity_analysis.get("confidence_distribution", {})
            if confidence_dist:
                ax2.bar(confidence_dist.keys(), confidence_dist.values())
                ax2.set_title('Confidence Level Distribution')
                ax2.set_xlabel('Confidence Level')
                ax2.set_ylabel('Count')
            
            # Service health
            performance_analysis = report.get("performance_analysis", {})
            service_reliability = performance_analysis.get("service_reliability", {})
            if service_reliability:
                status_counts = Counter(service_reliability.values())
                ax3.bar(status_counts.keys(), status_counts.values())
                ax3.set_title('Service Health Status')
                ax3.set_xlabel('Status')
                ax3.set_ylabel('Count')
            
            # Graph connectivity
            graph_analysis = report.get("graph_analysis", {})
            relationship_dist = graph_analysis.get("relationship_distribution", {})
            if relationship_dist:
                ax4.bar(relationship_dist.keys(), relationship_dist.values())
                ax4.set_title('Relationship Type Distribution')
                ax4.set_xlabel('Relationship Type')
                ax4.set_ylabel('Count')
                plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            
            # Convert to base64
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            plt.close()
            
            return img_base64
            
        except Exception as e:
            console.print(f"[red]Error generating visualization: {e}[/red]")
            return ""
    
    async def run_analytics(self):
        """Run comprehensive analytics"""
        console.print(Panel.fit(
            "[bold cyan]📊 Knowledge Graph Service Analytics[/bold cyan]\n"
            "Advanced analytics and reporting system",
            border_style="cyan"
        ))
        
        # Collect data
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Collecting data...", total=None)
            data = await self.collect_comprehensive_data()
            progress.update(task, completed=True)
        
        # Generate report
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating analytics report...", total=None)
            report = self.generate_analytics_report(data)
            progress.update(task, completed=True)
        
        # Display results
        console.print("\n[bold green]📈 Analytics Report Generated[/bold green]")
        
        # Summary
        summary = report["summary"]
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  • Total Entities: {summary['total_entities']}")
        console.print(f"  • Total Relationships: {summary['total_relationships']}")
        console.print(f"  • Healthy Services: {summary['healthy_services']}/{summary['total_services']}")
        console.print(f"  • Average Response Time: {summary['average_response_time']:.3f}s")
        
        # Entity distribution
        if report["entity_analysis"]:
            console.print("\n")
            entity_table = self.create_entity_distribution_chart(report["entity_analysis"])
            console.print(entity_table)
        
        # Performance analysis
        if report["performance_analysis"]:
            console.print("\n")
            perf_table = self.create_performance_table(report["performance_analysis"])
            console.print(perf_table)
        
        # Recommendations
        if report["recommendations"]:
            console.print("\n")
            rec_table = self.create_recommendations_table(report["recommendations"])
            console.print(rec_table)
        
        # Generate visualization
        console.print("\n[bold]Generating visualization...[/bold]")
        img_base64 = await self.generate_visualization_report(report)
        
        if img_base64:
            # Save report with visualization
            report["visualization"] = img_base64
            filename = f"knowledge_graph_analytics_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            console.print(f"[green]Analytics report saved to: {filename}[/green]")
            console.print("[yellow]Note: Visualization data is included as base64 in the JSON file[/yellow]")
        
        return report


async def main():
    """Main function"""
    async with KnowledgeGraphAnalytics() as analytics:
        await analytics.run_analytics()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Analytics stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Analytics error: {e}[/red]") 