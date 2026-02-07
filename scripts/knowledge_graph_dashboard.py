#!/usr/bin/env python3
"""
Knowledge Graph Service Dashboard

A comprehensive dashboard for monitoring and interacting with the Knowledge Graph Service
and its integrations with other microservices in the Personal Health Assistant platform.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

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


class KnowledgeGraphDashboard:
    """Interactive dashboard for Knowledge Graph Service monitoring and interaction"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stats = {}
        self.last_update = None
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        health_status = {}
        
        for service_name, service_url in SERVICES.items():
            try:
                response = await self.client.get(f"{service_url}/health")
                if response.status_code == 200:
                    health_status[service_name] = {
                        "status": "healthy",
                        "response": response.json(),
                        "last_check": datetime.utcnow().isoformat()
                    }
                else:
                    health_status[service_name] = {
                        "status": "unhealthy",
                        "status_code": response.status_code,
                        "last_check": datetime.utcnow().isoformat()
                    }
            except Exception as e:
                health_status[service_name] = {
                    "status": "error",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
        
        return health_status
    
    async def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get Knowledge Graph Service statistics"""
        try:
            response = await self.client.get(f"{SERVICES['knowledge_graph']}/api/v1/knowledge-graph/statistics")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get stats: {response.status_code}"}
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}
    
    async def search_entities(self, query: str, entity_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for entities in the knowledge graph"""
        try:
            params = {"q": query, "limit": limit}
            if entity_type:
                params["entity_type"] = entity_type
                
            response = await self.client.get(f"{SERVICES['knowledge_graph']}/api/v1/knowledge-graph/search/quick", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                return []
        except Exception as e:
            console.print(f"[red]Error searching entities: {e}[/red]")
            return []
    
    async def get_entities(self, entity_type: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get entities from the knowledge graph"""
        try:
            params = {"limit": limit}
            if entity_type:
                params["entity_type"] = entity_type
                
            response = await self.client.get(f"{SERVICES['knowledge_graph']}/api/v1/knowledge-graph/entities", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            console.print(f"[red]Error getting entities: {e}[/red]")
            return []
    
    def create_service_health_table(self, health_status: Dict[str, Any]) -> Table:
        """Create a table showing service health status"""
        table = Table(title="Service Health Status")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("Version", style="green")
        table.add_column("Last Check", style="dim")
        
        for service_name, status in health_status.items():
            if status["status"] == "healthy":
                status_style = "green"
                version = status.get("response", {}).get("version", "N/A")
            else:
                status_style = "red"
                version = "N/A"
            
            table.add_row(
                service_name.replace("_", " ").title(),
                f"[{status_style}]{status['status'].upper()}[/{status_style}]",
                version,
                status["last_check"][:19]  # Truncate timestamp
            )
        
        return table
    
    def create_knowledge_graph_stats_table(self, stats: Dict[str, Any]) -> Table:
        """Create a table showing knowledge graph statistics"""
        if "error" in stats:
            table = Table(title="Knowledge Graph Statistics")
            table.add_column("Error", style="red")
            table.add_row(stats["error"])
            return table
        
        table = Table(title="Knowledge Graph Statistics")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="bold")
        
        table.add_row("Total Entities", str(stats.get("total_entities", 0)))
        table.add_row("Total Relationships", str(stats.get("total_relationships", 0)))
        table.add_row("Graph Density", f"{stats.get('graph_density', 0):.6f}")
        table.add_row("Average Degree", f"{stats.get('average_degree', 0):.2f}")
        table.add_row("Last Updated", stats.get("last_updated", "N/A")[:19])
        
        # Entity types breakdown
        entities_by_type = stats.get("entities_by_type", {})
        for entity_type, count in entities_by_type.items():
            table.add_row(f"  {entity_type.title()}", str(count))
        
        return table
    
    def create_entity_table(self, entities: List[Dict[str, Any]], title: str = "Entities") -> Table:
        """Create a table showing entities"""
        table = Table(title=title)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Description", style="dim", max_width=50)
        table.add_column("Confidence", style="yellow")
        
        for entity in entities[:10]:  # Limit to 10 for display
            description = entity.get("description", "")[:47] + "..." if len(entity.get("description", "")) > 50 else entity.get("description", "")
            table.add_row(
                entity.get("display_name", entity.get("name", "")),
                entity.get("entity_type", "").title(),
                description,
                entity.get("confidence", "").title()
            )
        
        return table
    
    async def interactive_search(self):
        """Interactive search interface"""
        console.print("\n[bold cyan]🔍 Interactive Knowledge Graph Search[/bold cyan]")
        
        while True:
            query = Prompt.ask("\nEnter search query (or 'quit' to exit)")
            if query.lower() == 'quit':
                break
            
            entity_type = Prompt.ask("Entity type (optional, press Enter to skip)", default="")
            limit = Prompt.ask("Number of results", default="10")
            
            try:
                limit = int(limit)
            except ValueError:
                limit = 10
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Searching...", total=None)
                results = await self.search_entities(query, entity_type if entity_type else None, limit)
                progress.update(task, completed=True)
            
            if results:
                console.print(f"\n[green]Found {len(results)} results:[/green]")
                table = self.create_entity_table(results, f"Search Results for '{query}'")
                console.print(table)
            else:
                console.print(f"\n[yellow]No results found for '{query}'[/yellow]")
    
    async def entity_explorer(self):
        """Interactive entity explorer"""
        console.print("\n[bold cyan]🔬 Entity Explorer[/bold cyan]")
        
        entity_types = ["condition", "symptom", "medication", "treatment", "procedure", "lab_test", "vital_sign", "risk_factor"]
        
        while True:
            console.print("\nAvailable entity types:")
            for i, entity_type in enumerate(entity_types, 1):
                console.print(f"  {i}. {entity_type.title()}")
            console.print("  0. Exit")
            
            choice = Prompt.ask("Select entity type", choices=[str(i) for i in range(len(entity_types) + 1)])
            
            if choice == "0":
                break
            
            try:
                selected_type = entity_types[int(choice) - 1]
                limit = Prompt.ask("Number of entities to show", default="20")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Loading {selected_type} entities...", total=None)
                    entities = await self.get_entities(selected_type, int(limit))
                    progress.update(task, completed=True)
                
                if entities:
                    console.print(f"\n[green]Found {len(entities)} {selected_type} entities:[/green]")
                    table = self.create_entity_table(entities, f"{selected_type.title()} Entities")
                    console.print(table)
                else:
                    console.print(f"\n[yellow]No {selected_type} entities found[/yellow]")
                    
            except (ValueError, IndexError):
                console.print("[red]Invalid choice[/red]")
    
    async def integration_test(self):
        """Test integration with other services"""
        console.print("\n[bold cyan]🧪 Integration Testing[/bold cyan]")
        
        # Test Medical Records integration
        console.print("\n[bold]Testing Medical Records Integration:[/bold]")
        try:
            # Test enrichment endpoint availability
            response = await self.client.get(f"{SERVICES['medical_records']}/api/v1/medical-records/lab-results/test/no-auth")
            if response.status_code == 200:
                console.print("✅ Medical Records Service accessible")
            else:
                console.print("❌ Medical Records Service not accessible")
        except Exception as e:
            console.print(f"❌ Medical Records Service error: {e}")
        
        # Test AI Insights integration
        console.print("\n[bold]Testing AI Insights Integration:[/bold]")
        try:
            response = await self.client.get(f"{SERVICES['ai_insights']}/health")
            if response.status_code == 200:
                console.print("✅ AI Insights Service accessible")
            else:
                console.print("❌ AI Insights Service not accessible")
        except Exception as e:
            console.print(f"❌ AI Insights Service error: {e}")
        
        # Test Health Tracking integration
        console.print("\n[bold]Testing Health Tracking Integration:[/bold]")
        try:
            response = await self.client.get(f"{SERVICES['health_tracking']}/health")
            if response.status_code == 200:
                console.print("✅ Health Tracking Service accessible")
            else:
                console.print("❌ Health Tracking Service not accessible")
        except Exception as e:
            console.print(f"❌ Health Tracking Service error: {e}")
    
    async def real_time_monitor(self):
        """Real-time monitoring dashboard"""
        console.print("\n[bold cyan]📊 Real-time Monitoring[/bold cyan]")
        console.print("Press Ctrl+C to exit monitoring")
        
        try:
            with Live(auto_refresh=False) as live:
                while True:
                    # Get current status
                    health_status = await self.get_service_health()
                    kg_stats = await self.get_knowledge_graph_stats()
                    
                    # Create layout
                    layout = Layout()
                    layout.split_column(
                        Layout(name="header", size=3),
                        Layout(name="body"),
                        Layout(name="footer", size=3)
                    )
                    
                    layout["body"].split_row(
                        Layout(name="health"),
                        Layout(name="stats")
                    )
                    
                    # Header
                    header = Panel(
                        f"Knowledge Graph Service Dashboard - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                        style="bold cyan"
                    )
                    layout["header"].update(header)
                    
                    # Health status
                    health_table = self.create_service_health_table(health_status)
                    layout["health"].update(Panel(health_table, title="Service Health"))
                    
                    # Knowledge graph stats
                    stats_table = self.create_knowledge_graph_stats_table(kg_stats)
                    layout["stats"].update(Panel(stats_table, title="Knowledge Graph Stats"))
                    
                    # Footer
                    footer = Panel(
                        "Real-time monitoring active - Services: " + 
                        ", ".join([f"{name}: {'🟢' if status['status'] == 'healthy' else '🔴'}" 
                                 for name, status in health_status.items()]),
                        style="dim"
                    )
                    layout["footer"].update(footer)
                    
                    live.update(layout)
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")
    
    async def run_dashboard(self):
        """Main dashboard interface"""
        console.print(Panel.fit(
            "[bold cyan]🧠 Knowledge Graph Service Dashboard[/bold cyan]\n"
            "Comprehensive monitoring and interaction interface",
            border_style="cyan"
        ))
        
        while True:
            console.print("\n[bold]Available Options:[/bold]")
            console.print("1. 📊 View Service Health")
            console.print("2. 📈 View Knowledge Graph Statistics")
            console.print("3. 🔍 Interactive Search")
            console.print("4. 🔬 Entity Explorer")
            console.print("5. 🧪 Test Integrations")
            console.print("6. 📊 Real-time Monitoring")
            console.print("7. 📋 Export Data")
            console.print("0. Exit")
            
            choice = Prompt.ask("Select option", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
            
            if choice == "0":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif choice == "1":
                health_status = await self.get_service_health()
                table = self.create_service_health_table(health_status)
                console.print(table)
            elif choice == "2":
                kg_stats = await self.get_knowledge_graph_stats()
                table = self.create_knowledge_graph_stats_table(kg_stats)
                console.print(table)
            elif choice == "3":
                await self.interactive_search()
            elif choice == "4":
                await self.entity_explorer()
            elif choice == "5":
                await self.integration_test()
            elif choice == "6":
                await self.real_time_monitor()
            elif choice == "7":
                await self.export_data()
    
    async def export_data(self):
        """Export knowledge graph data"""
        console.print("\n[bold cyan]📋 Data Export[/bold cyan]")
        
        export_type = Prompt.ask(
            "Export type",
            choices=["entities", "statistics", "health_status", "all"],
            default="all"
        )
        
        filename = Prompt.ask("Filename", default=f"knowledge_graph_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "export_type": export_type
        }
        
        if export_type in ["entities", "all"]:
            entities = await self.get_entities(limit=1000)
            export_data["entities"] = entities
        
        if export_type in ["statistics", "all"]:
            stats = await self.get_knowledge_graph_stats()
            export_data["statistics"] = stats
        
        if export_type in ["health_status", "all"]:
            health_status = await self.get_service_health()
            export_data["health_status"] = health_status
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            console.print(f"[green]Data exported to {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Export failed: {e}[/red]")


async def main():
    """Main function"""
    console.print(Panel.fit(
        "[bold cyan]🧠 Knowledge Graph Service Dashboard[/bold cyan]\n"
        "Personal Health Assistant Platform\n"
        "Advanced Medical Knowledge Management",
        border_style="cyan"
    ))
    
    async with KnowledgeGraphDashboard() as dashboard:
        await dashboard.run_dashboard()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Dashboard error: {e}[/red]") 