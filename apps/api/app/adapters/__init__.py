"""Ports-and-adapters lives ONLY here.

ports.py defines typing.Protocol interfaces. Concrete implementations are
plain classes that structurally satisfy a Protocol — no inheritance, no ABC.
Subpackages group impls by category (llm/, calendar/, voice/).
"""
