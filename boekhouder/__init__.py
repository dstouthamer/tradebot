"""AI Boekhouder — een Nederlandse AI-boekhoud-, CFO- en fiscale optimalisatie-agent.

The package implements the masterprompt's agent roles as small, testable units that
all speak one language (an ``AgentResult`` carrying a groen/oranje/rood risk zone,
confidence and reasons). Nothing is ever booked, sent or filed without an explicit
confirmation — see ``boekhouder.engine.audit`` and ``boekhouder.agents.compliance``.
"""

__version__ = "0.1.0-mvp"
