#!/usr/bin/env python
"""
Tournament Agent: Two-Strike Guard
Student: Christelle Jean
Generated: 2026-10-01 00:56:41

Evolution Details:
- Generations: 100
- Final Fitness: 141.77
- Trained against: Suspicious Tit-for-Tat, Soft Majority, Hard Majority, Pavlov, Gradual, Tit-for-Tat, Always Invest, Generous Tit-for-Tat, Tit-for-Two-Tats, Grim Trigger, Always Undercut, Random (0.7), Random (0.3)

Strategy: Starts by investing but undercuts after two defections in a row.
"""

from agents import Agent, INVEST, UNDERCUT
import random


class ChristelleJeanAgent(Agent):
    """
    Two-Strike Guard

    Starts by investing but undercuts after two defections in a row.

    Evolved Genes: [1.0, 1.0, 0.824421366268778, 0.0, 0.6326476140264558, 0.3448205781863124, 0.0, 0.0]
    """

    def __init__(self):
        self.genes = [1.0, 1.0, 0.824421366268778, 0.0, 0.6326476140264558, 0.3448205781863124, 0.0, 0.0]
        self.student_name = 'Christelle Jean'

        super().__init__(
            name='Two-Strike Guard',
            description='Starts by investing but undercuts after two defections in a row.'
        )

    def choose_action(self) -> bool:
        # Establish cooperation during the opening rounds
        if self.round_num < 3:
            return random.random() < self.genes[0]

        # Review a recent section of the opponent's history
        memory_length = 3 + int(self.genes[4] * 9)
        recent_history = self.history[-memory_length:]

        cooperation_rate = sum(recent_history) / len(recent_history)
        defection_rate = 1.0 - cooperation_rate

        # Count consecutive undercuts
        defection_streak = 0
        for action in reversed(recent_history):
            if action == UNDERCUT:
                defection_streak += 1
            else:
                break

        streak_limit = 2 + int(self.genes[6] * 3)

        # Stop forgiving an opponent that keeps undercutting
        if defection_streak >= streak_limit:
            return UNDERCUT

        # Try to rebuild cooperation when the opponent changes behavior
        if (
            len(self.history) >= 2
            and self.history[-2] == UNDERCUT
            and self.history[-1] == INVEST
        ):
            if random.random() < self.genes[7]:
                return INVEST

        # Cooperate with an opponent that has been consistently cooperative
        if defection_rate == 0:
            return random.random() < self.genes[1]

        retaliation_threshold = 0.15 + (self.genes[5] * 0.55)

        # Respond when undercutting becomes a pattern
        if defection_rate >= retaliation_threshold:
            if random.random() < self.genes[2]:
                return UNDERCUT

            if random.random() < self.genes[3]:
                return INVEST

            return UNDERCUT

        # Decide whether to forgive an isolated undercut
        if self.history[-1] == UNDERCUT:
            return random.random() < self.genes[3]

        return random.random() < self.genes[1]



def get_agent():
    """Return an instance for tournament use."""
    return ChristelleJeanAgent()


if __name__ == "__main__":
    agent = get_agent()
    print(f"Agent loaded successfully: {agent.name}")
    print(f"Genes: {agent.genes}")
    print(f"Description: {agent.description}")
