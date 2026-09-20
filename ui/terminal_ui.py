import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from typing import Dict, Any

import config
from brain.orchestrator import InnvoOrchestrator

class TerminalUI:
    """
    Jarvis-Style Sci-Fi Terminal Interface with Full Tool Execution & Self-Development.
    """
    def __init__(self, orchestrator: InnvoOrchestrator):
        self.orchestrator = orchestrator
        self.console = Console()
        self.continuous_voice = False

    def print_banner(self):
        stats = self.orchestrator.memory_store.get_stats()
        platform_name = "Android Termux" if config.IS_TERMUX else ("Windows" if config.IS_WINDOWS else "Linux/Mac")
        voice_status = f"[green]{config.DEFAULT_VOICE}[/green]" if self.orchestrator.audio.enabled else "[yellow]OFF[/yellow]"
        brain_mode = f"[cyan]{self.orchestrator.slm.model_name}[/cyan]" if self.orchestrator.slm.has_ollama else "[yellow]Fallback SLM[/yellow]"
        tools_count = len(self.orchestrator.registry.skills)

        banner_text = Text()
        banner_text.append("⚡ ", style="bold yellow")
        banner_text.append("INNVO AI COMPANION (JARVIS CORE)", style="bold cyan")
        banner_text.append(" ⚡\n", style="bold yellow")
        banner_text.append(f"OS: {platform_name} | Brain: ", style="dim white")
        banner_text.append_text(Text.from_markup(brain_mode))
        banner_text.append(f" | Tools: {tools_count} active | Voice: ", style="dim white")
        banner_text.append_text(Text.from_markup(voice_status))
        banner_text.append(f" | RL Memories: {stats['active_memories']}", style="dim white")

        self.console.print(Panel(
            banner_text,
            border_style="cyan",
            title="[bold green]System Online & Tools Active[/bold green]",
            subtitle="[dim]Press [v] to speak | Type '/tools' to view skills | '/help' for commands | 'exit' to quit[/dim]"
        ))

    def show_tools(self):
        skills = self.orchestrator.registry.list_skills()
        if not skills:
            self.console.print("[yellow]No tools registered.[/yellow]")
            return

        table = Table(title="Innvo Active Tool & Skill Registry", border_style="cyan")
        table.add_column("Tool Name", style="bold cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Q-Value (RL Score)", style="green", justify="right")
        table.add_column("Runs", style="dim", justify="right")

        for s in skills:
            q = s.get("q_value", 1.0)
            q_color = "green" if q >= 0.8 else ("yellow" if q >= 0.3 else "red")
            table.add_row(
                s["name"],
                s.get("type", "builtin"),
                s["description"],
                f"[{q_color}]{q:.2f}[/{q_color}]",
                str(s.get("invocations", 0))
            )
        self.console.print(table)

    def show_context(self):
        history = self.orchestrator.conversation_history
        if not history:
            self.console.print("[yellow]Conversation context is currently empty.[/yellow]")
            return

        table = Table(title="Active Multi-Turn Conversation Context", border_style="cyan")
        table.add_column("Turn", style="dim", width=6)
        table.add_column("Speaker", style="magenta", width=12)
        table.add_column("Message Content", style="white")

        for idx, turn in enumerate(history, 1):
            speaker_style = "[bold green]You[/bold green]" if turn["role"] == "user" else "[bold cyan]Innvo[/bold cyan]"
            table.add_row(str(idx), speaker_style, turn["content"])

        self.console.print(table)

    def show_memories(self):
        memories = self.orchestrator.memory_store.list_all_active()
        if not memories:
            self.console.print("[yellow]Abhi tak koi permanent memory save nahi hui hai.[/yellow]")
            return

        table = Table(title="Innvo Permanent RL Memory Store", border_style="cyan")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Category", style="magenta")
        table.add_column("Knowledge / Fact", style="white")
        table.add_column("Q-Value (RL Score)", style="green", justify="right")
        table.add_column("Used", style="dim", justify="right")

        for m in memories:
            q_color = "green" if m["q_value"] >= 0.8 else ("yellow" if m["q_value"] >= 0.3 else "red")
            table.add_row(
                str(m["id"]),
                m["category"],
                m["content"],
                f"[{q_color}]{m['q_value']:.2f}[/{q_color}]",
                str(m["access_count"])
            )
        self.console.print(table)

    def show_stats(self):
        mem_stats = self.orchestrator.memory_store.get_stats()
        bandit_status = self.orchestrator.bandit.get_status()

        table = Table(title="Innvo RL Agent Statistics", border_style="yellow")
        table.add_column("Metric", style="cyan")
        table.add_column("Current Value", style="white")

        table.add_row("Active Memories", str(mem_stats["active_memories"]))
        table.add_row("Average Memory Q-Score", str(mem_stats["average_q_value"]))
        table.add_row("Total Feedback Iterations", str(mem_stats["total_feedbacks"]))
        table.add_row("Active Tools Count", str(len(self.orchestrator.registry.skills)))
        table.add_row("Dominant Conversational Tone", str(bandit_status["top_tone"]))

        self.console.print(table)

    def show_help(self):
        help_text = """
[bold cyan]Voice, Chat & Tool Commands:[/bold cyan]
  [green]v[/green] or [green]/listen[/green]     - Activate microphone to speak in Hindi/English
  [green]/continuous[/green]     - Toggle continuous voice loop (Hands-Free conversation)
  [green]/tools[/green]          - View all active built-in & self-developed tools
  [green]/context[/green]        - View active multi-turn conversation history
  [green]/clear[/green]          - Clear active conversation context (Start fresh topic)
  [green]/memories[/green]       - View all permanent memories and their RL Q-scores
  [green]/stats[/green]          - View Reinforcement Learning performance metrics
  [green]/voice on/off[/green]  - Toggle voice output
  [green]/help[/green]           - Display this help message
  [green]exit / quit[/green]     - Shutdown Innvo
        """
        self.console.print(Panel(help_text.strip(), title="Innvo Help Center", border_style="blue"))

    def capture_voice_input(self) -> str:
        self.console.print("\n🎙️  [bold red]Listening... (Speak naturally in Hindi, English, or Hinglish)[/bold red]")
        text = self.orchestrator.audio.listen()
        if text:
            self.console.print(f"[bold green]You (Voice):[/bold green] [white]{text}[/white]")
            return text
        else:
            self.console.print("[yellow]Could not hear audio. Try speaking closer to the mic or type your message.[/yellow]")
            return ""

    def handle_special_command(self, cmd: str) -> bool:
        cmd_clean = cmd.lower().strip()
        if cmd_clean in ["exit", "quit", "bye", "alvida"]:
            self.console.print("[bold cyan]Innvo shutting down. Alvida sir, take care![/bold cyan]")
            self.orchestrator.audio.speak("Alvida sir, take care!")
            sys.exit(0)

        if cmd_clean in ["v", "/listen", "/mic"]:
            spoken_text = self.capture_voice_input()
            if spoken_text:
                self.process_and_display(spoken_text)
            return True

        if cmd_clean in ["/continuous", "/handsfree"]:
            self.continuous_voice = not self.continuous_voice
            status = "[bold green]ON (Hands-Free Voice)[/bold green]" if self.continuous_voice else "[yellow]OFF[/yellow]"
            self.console.print(f"Continuous Voice Mode: {status}")
            return True

        if cmd_clean in ["/clear", "/new", "/reset"]:
            self.orchestrator.clear_context()
            self.console.print("[green]Active conversation context cleared![/green]")
            return True

        if cmd_clean == "/tools":
            self.show_tools()
            return True
        elif cmd_clean == "/context":
            self.show_context()
            return True
        elif cmd_clean == "/memories":
            self.show_memories()
            return True
        elif cmd_clean == "/stats":
            self.show_stats()
            return True
        elif cmd_clean == "/voice on":
            self.orchestrator.audio.enabled = True
            self.console.print("[green]Voice output ENABLED (hi-IN-MadhurNeural)[/green]")
            return True
        elif cmd_clean == "/voice off":
            self.orchestrator.audio.enabled = False
            self.orchestrator.audio.stop()
            self.console.print("[yellow]Voice output DISABLED (Text only mode)[/yellow]")
            return True
        elif cmd_clean == "/help":
            self.show_help()
            return True

        return False

    def process_and_display(self, user_input: str):
        with self.console.status("[bold cyan]Innvo thinking...[/bold cyan]", spinner="dots"):
            result = self.orchestrator.process_input(user_input)

        reply = result.get("reply", "")
        search_badge = " [dim cyan](Web Verified)[/dim cyan]" if result.get("search_used") else ""
        tool_badge = f" [bold green](Tool: {result['tool_used']})[/bold green]" if result.get("tool_used") else ""
        approval_badge = " [bold yellow][Waiting for Approval: Reply Haan/Nahi][/bold yellow]" if result.get("pending_approval") else ""

        self.console.print(Panel(
            reply,
            title=f"[bold cyan]Innvo[/bold cyan]{tool_badge}{search_badge}{approval_badge}",
            border_style="cyan"
        ))

    def run_loop(self):
        self.print_banner()

        while True:
            try:
                if self.continuous_voice:
                    user_input = self.capture_voice_input()
                    if not user_input:
                        continue
                else:
                    user_input = Prompt.ask("\n[bold green]You[/bold green] [dim](or type 'v' to speak)[/dim]").strip()
                    if not user_input:
                        continue

                if self.handle_special_command(user_input):
                    continue

                self.process_and_display(user_input)

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Innvo paused. Type 'exit' to quit.[/dim]")
                break
