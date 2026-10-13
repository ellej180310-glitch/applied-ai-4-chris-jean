#!/usr/bin/env python3
"""
Skeleton Optimization Agent - Template for students to implement optimization algorithms

IMPORTANT: This is NOT an RL agent - it's a template for
students to implement their own optimization algorithms (greedy, Hungarian, etc.)

This agent currently makes terrible decisions:
- Random staffing decisions
- No layout optimization
- Ignores order priorities
- No intelligent assignment logic

Students should replace the naive methods with proper optimization algorithms.
"""

import numpy as np
from typing import Dict, Optional
from .standardized_agents import BaselineAgent

class SkeletonOptimizationAgent(BaselineAgent):
    """
    Template for students to implement their own optimization algorithms.

    Students should replace the naive methods with:
    - Economic models for staffing decisions
    - Hungarian algorithm for order assignment
    - Greedy search for layout optimization
    - Multi-objective optimization techniques
    """

    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"

        # Enable unlimited hiring for true economic optimization
        self.env._unlimited_hiring = True

        # Students can add their own state tracking here
        self.performance_metrics = []
        self.decision_history = []

        # Students can add algorithm parameters here
        # Example: Hungarian algorithm matrices, greedy search parameters, etc.
        self.staffing_parameters = {
            'hire_threshold_ratio': 3.0,
            'fire_threshold_ratio': 2.0,
            'profit_threshold': 0
        }

        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False

    def reset(self):
        """Reset agent state - students should expand this"""
        self.action_history = []
        self.reward_history = []
        # TODO: Reset any neural network states, replay buffers, etc.

    def get_action(self, observation: Dict) -> Dict:
        """
        Generate action based on observation.
        Current implementation is intentionally terrible - students should improve!
        """

        # Extract basic info from observation
        current_timestep = observation['time'][0]
        financial_state = observation['financial']  # [profit, revenue, costs, burn_rate]
        queue_info = observation['order_queue']
        employee_info = observation['employees']

        action = {
            'staffing_action': self._get_naive_staffing_action(financial_state, employee_info),
            'layout_swap': self._get_naive_layout_action(current_timestep),
            'order_assignments': self._get_naive_order_assignments(queue_info, employee_info)
        }

        # TODO: Students should implement proper action recording for optimization
        self.action_history.append(action.copy())

        return action

    def _get_naive_staffing_action(self, financial_state, employee_info) -> int:
        """
        WEEK 2 STEP 1: Staffing decisions - students should improve this!

        Current problems:
        - Ignores queue length and workload
        - Random decisions regardless of profit
        - No consideration of employee efficiency
        """

        # TODO WEEK 2 STEP 1: Students should implement intelligent staffing logic
        # Current approach: Make random decisions based on "vibes"

        current_profit = financial_state[0]
        num_employees = len(self.env.employees)

        # Layout optimization requires one manager, but additional managers
        # would create unnecessary salary costs.
        has_manager = any(
            getattr(employee, "is_manager", False)
            for employee in self.env.employees
        )

        if np.random.random() < 0.3:  # 30% chance to hire
            if num_employees < 20:  # Don't go completely overboard
                return 1  # Hire worker
        elif np.random.random() < 0.1:  # 10% chance to fire
            if num_employees > 1:  # Don't fire everyone
                return 2  # Fire worker
        elif np.random.random() < 0.2:
            if not has_manager:
                return 3

        return 0  # No action

    def _get_naive_layout_action(self, current_timestep) -> list:
        """
        Move frequently requested items closer to the truck bays.
        """

        # Check frequently so an idle manager does not miss a useful swap
        if current_timestep == 0 or current_timestep % 25 != 0:
            return [0, 0]

        queue_length = len(self.env.order_queue.orders)
        num_employees = len(self.env.employees)

        # Avoid relocation when demand is too high for the workforce
        if queue_length > max(10, num_employees * 10):
            return [0, 0]

        # A layout swap can only be completed by an idle manager
        manager = next(
            (employee for employee in self.env.employees if employee.is_manager),
            None
        )

        if manager is None:
            return [0, 0]

        try:
            from ..environment.employee import EmployeeState
        except ImportError:
            from environment.employee import EmployeeState

        if manager.state != EmployeeState.IDLE:
            return [0, 0]

        grid = self.env.warehouse_grid
        frequencies = grid.item_access_frequency

        # Find items that have been requested
        active_items = np.flatnonzero(frequencies > 0)

        if len(active_items) == 0:
            return [0, 0]

        # Items in the top 25 percent are considered hot
        hot_threshold = np.percentile(frequencies[active_items], 75)

        hot_items = [
            int(item)
            for item in active_items
            if frequencies[item] >= hot_threshold
        ]

        # Start with the most requested item
        hot_items.sort(
            key=lambda item: frequencies[item],
            reverse=True
        )

        for item_type in hot_items:
            locations = grid.find_item_locations(item_type)

            # Check the farthest copy first
            locations.sort(
                key=lambda position: min(
                    grid.manhattan_distance(position, bay)
                    for bay in grid.truck_bay_positions
                ),
                reverse=True
            )

            for current_pos in locations:
                current_distance = min(
                    grid.manhattan_distance(current_pos, bay)
                    for bay in grid.truck_bay_positions
                )

                if current_distance > 3:
                    swap = self._find_closer_position(
                        current_pos,
                        grid.truck_bay_positions
                    )

                    if swap is not None:
                        return swap
        # Group items that are often ordered together
        if current_timestep % 200 == 0:
            cooccurrence_swap = self._find_cooccurrence_swap()

            if cooccurrence_swap is not None:
                return cooccurrence_swap

        return [0, 0]

    def _find_closer_position(self, current_pos, delivery_positions):
        """
        Find a storage position closer to the truck bays.
        """
        grid = self.env.warehouse_grid

        current_item = grid.get_item_at_position(
            current_pos[0],
            current_pos[1]
        )

        if current_item is None:
            return None

        current_frequency = grid.item_access_frequency[current_item]

        current_distance = min(
            grid.manhattan_distance(current_pos, bay)
            for bay in delivery_positions
        )

        best_position = None
        best_improvement = 1
        lowest_target_frequency = float("inf")

        for y in range(grid.height):
            for x in range(grid.width):
                candidate_pos = (x, y)

                if candidate_pos == current_pos:
                    continue

                # Only use accessible storage cells
                if grid.cell_types[y, x] != 1:
                    continue

                if not grid.can_access_storage(x, y):
                    continue

                candidate_distance = min(
                    grid.manhattan_distance(candidate_pos, bay)
                    for bay in delivery_positions
                )

                improvement = current_distance - candidate_distance

                target_item = grid.get_item_at_position(x, y)

                if target_item is None:
                    target_frequency = 0
                else:
                    target_frequency = grid.item_access_frequency[target_item]

                # Do not move a more popular item farther away
                if target_frequency >= current_frequency:
                    continue

                if (
                    improvement > best_improvement
                    or (
                        improvement == best_improvement
                        and target_frequency < lowest_target_frequency
                    )
                ):
                    best_position = candidate_pos
                    best_improvement = improvement
                    lowest_target_frequency = target_frequency

        if best_position is None:
            return None

        current_index = current_pos[1] * grid.width + current_pos[0]
        target_index = best_position[1] * grid.width + best_position[0]

        return [current_index, target_index]

    def _find_cooccurrence_swap(self):
        """
        Move items that are often ordered together closer to each other.
        """
        grid = self.env.warehouse_grid
        cooccurrence = grid.item_cooccurrence

        minimum_cooccurrence = 3
        minimum_distance = 4
        best_benefit = 0
        best_swap = None

        for item1 in range(grid.num_item_types):
            for item2 in range(item1 + 1, grid.num_item_types):
                pair_count = cooccurrence[item1, item2]

                if pair_count <= minimum_cooccurrence:
                    continue

                locations1 = grid.find_item_locations(item1)
                locations2 = grid.find_item_locations(item2)

                if not locations1 or not locations2:
                    continue

                for pos1 in locations1:
                    for pos2 in locations2:
                        if not grid.can_access_storage(pos2[0], pos2[1]):
                            continue

                        current_distance = grid.manhattan_distance(pos1, pos2)

                        if current_distance <= minimum_distance:
                            continue

                        source_frequency = grid.item_access_frequency[item2]

                        # Check storage cells beside the first item
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            target_x = pos1[0] + dx
                            target_y = pos1[1] + dy

                            if not grid.is_valid_position(target_x, target_y):
                                continue

                            if grid.cell_types[target_y, target_x] != 1:
                                continue

                            if not grid.can_access_storage(target_x, target_y):
                                continue

                            target_pos = (target_x, target_y)

                            if target_pos == pos2:
                                continue

                            target_item = grid.get_item_at_position(
                                target_x,
                                target_y
                            )

                            # Do not move another popular item farther away
                            if target_item is None:
                                target_frequency = 0
                            else:
                                target_frequency = (
                                    grid.item_access_frequency[target_item]
                                )

                            if target_frequency >= source_frequency:
                                continue

                            new_distance = grid.manhattan_distance(
                                pos1,
                                target_pos
                            )

                            distance_saved = current_distance - new_distance
                            benefit = pair_count * distance_saved

                            if benefit > best_benefit:
                                source_index = (
                                    pos2[1] * grid.width + pos2[0]
                                )
                                target_index = (
                                    target_y * grid.width + target_x
                                )

                                best_benefit = benefit
                                best_swap = [source_index, target_index]

        return best_swap

    def _get_naive_order_assignments(self, queue_info, employee_info) -> list:
        """
        WEEK 2 STEP 2: Order assignment - students should improve this!

        Current problems:
        - Ignores employee locations
        - No consideration of order priority/value
        - Random assignments regardless of efficiency
        - Doesn't check if employees are actually available
        """

        # TODO WEEK 2 STEP 2: Students should implement intelligent order assignment
        # Current approach: Random assignments

        assignments = [0] * 20  # No assignments by default

        # Count how many employees we have (very naive)
        num_employees = int(np.sum(employee_info[:, 0] > 0))

        # Randomly assign first few orders to first few employees
        if num_employees > 0:
            for i in range(min(3, num_employees)):  # Only assign 3 orders max
                if np.random.random() < 0.6:  # 60% chance to assign
                    assignments[i] = (i % num_employees) + 1  # Random employee

        return assignments

    def record_reward(self, reward: float):
        """
        WEEK 3 STEP 1: Reward tracking and learning - students should expand this

        TODO WEEK 3 STEP 1: Students should implement:
        - Proper reward tracking
        - Performance analysis
        - Adaptive parameter adjustment
        - Multi-objective optimization
        """
        self.reward_history.append(reward)

        # Skeleton optimization - doesn't actually learn anything useful
        if len(self.reward_history) > 10:
            # "Update" weights randomly (this doesn't actually improve performance)
            if reward > 0:
                self.staffing_weights += np.random.randn(4) * 0.01
                self.layout_weights += np.random.randn(3) * 0.01

    def should_update_policy(self) -> bool:
        """
        WEEK 3 STEP 2: Policy updates and adaptation - students should improve this

        TODO WEEK 3 STEP 2: Students should implement proper update schedules
        """
        return len(self.action_history) % 50 == 0  # Arbitrary update frequency

    def get_performance_metrics(self) -> Dict:
        """
        Get agent performance metrics for analysis
        Students can use this to debug their improvements
        """
        if not self.reward_history:
            return {"avg_reward": 0, "total_actions": 0}

        return {
            "avg_reward": np.mean(self.reward_history[-100:]),  # Last 100 rewards
            "total_actions": len(self.action_history),
            "exploration_rate": self.exploration_rate,
            "recent_performance": np.mean(self.reward_history[-10:]) if len(self.reward_history) >= 10 else 0
        }


def create_skeleton_optimization_agent(env) -> SkeletonOptimizationAgent:
    """Factory function to create skeleton Optimization agent"""
    return SkeletonOptimizationAgent(env)


# TODO: Students should implement these advanced components:

class StudentOptimizationAgent(SkeletonOptimizationAgent):
    """
    Template for students to implement their improved Optimization agent

    Suggested improvements:
    1. Replace random staffing with demand-based hiring
    2. Implement proper layout optimization using item frequencies
    3. Add distance-based order assignment
    4. Implement basic Q-optimization or policy gradients
    5. Add proper exploration vs exploitation balance
    """

    def __init__(self, env):
        super().__init__(env)
        self.name = "StudentOptimization"

        # TODO: Students implement these
        # self.q_table = {}
        # self.policy_network = SimpleNeuralNetwork()
        # self.experience_buffer = []
        # self.target_network = None

    def _get_improved_staffing_action(self, financial_state, employee_info, queue_info):
        """
        WEEK 2 STEP 1: Students implement intelligent staffing:
        - Hire when queue is growing
        - Fire when queue is empty for extended periods
        - Consider profit margins before hiring
        - Balance managers vs workers
        """
        pass

    def _get_improved_layout_action(self, observation):
        """
        WEEK 1 STEP 1: Students implement smart layout optimization:
        - Move frequently accessed items closer to delivery
        - Group items that are often ordered together
        - Only optimize when queue is manageable
        - Track swap effectiveness
        """
        pass

    def _get_improved_order_assignments(self, queue_info, employee_info):
        """
        WEEK 2 STEP 2: Students implement efficient order assignment:
        - Assign orders to closest available employees
        - Prioritize high-value or urgent orders
        - Consider employee current locations
        - Balance workload across employees
        """
        pass

    def learn_from_experience(self, state, action, reward, next_state, done):
        """
        WEEK 3 STEP 3: Students implement multi-objective optimization:
        - Performance trend analysis
        - Adaptive parameter tuning
        - Multi-objective trade-off handling
        - Robust optimization techniques
        """
        pass