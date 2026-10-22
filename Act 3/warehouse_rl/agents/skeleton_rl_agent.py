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
from scipy.optimize import linear_sum_assignment
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
             'fire_threshold_ratio': 1.5,
             'profit_threshold': 1000.0,
            'manager_profit_threshold': 2000.0,
            'minimum_workers': 2,
            'maximum_workers': 20,
            'review_interval': 50
            }

        # Track economic performance and limit staffing changes
        self.staffing_profit_history = []
        self.last_staffing_review = -50

        # Students can implement adaptive parameters that change based on performance
        self.adaptive_optimization_enabled = False

    def reset(self):
        """Reset agent state between simulation episodes."""
        self.action_history = []
        self.reward_history = []
        self.staffing_profit_history = []
        self.last_staffing_review = -50

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
        WEEK 2 STEP 1: Economic staffing optimization.

        Hire only when demand and expected revenue justify the additional
        wage cost. Fire only when capacity is clearly underused, while
        preserving the manager and a minimum workforce.
        """

        current_profit = float(financial_state[0])
        revenue = float(financial_state[1])
        costs = float(financial_state[2])
        burn_rate = float(financial_state[3])
        current_timestep = int(self.env.current_timestep)

        employees = self.env.employees
        workers = [
            employee
            for employee in employees
            if not getattr(employee, "is_manager", False)
        ]
        managers = [
            employee
            for employee in employees
            if getattr(employee, "is_manager", False)
        ]

        num_workers = len(workers)
        queue_length = len(self.env.order_queue.orders)
        has_manager = len(managers) > 0

        # Record profit to measure whether performance is improving.
        self.staffing_profit_history.append(current_profit)
        if len(self.staffing_profit_history) > 200:
            self.staffing_profit_history.pop(0)

        recent_profit_change = 0.0
        if len(self.staffing_profit_history) >= 51:
            recent_profit_change = (
                current_profit - self.staffing_profit_history[-51]
            )

        # Review staffing at fixed intervals instead of every timestep.
        review_interval = self.staffing_parameters['review_interval']
        if current_timestep - self.last_staffing_review < review_interval:
            return 0

        self.last_staffing_review = current_timestep

        # Allow time for useful demand and financial data to develop.
        if current_timestep < 200:
            return 0

        queue_pressure = queue_length / max(1, num_workers)
        profit_per_worker = current_profit / max(1, num_workers)
        average_revenue_per_step = revenue / max(1, current_timestep)

        hire_threshold = self.staffing_parameters[
            'hire_threshold_ratio'
        ]
        fire_threshold = self.staffing_parameters[
            'fire_threshold_ratio'
        ]
        profit_threshold = self.staffing_parameters[
            'profit_threshold'
        ]
        manager_threshold = self.staffing_parameters[
            'manager_profit_threshold'
        ]
        minimum_workers = self.staffing_parameters[
            'minimum_workers'
        ]
        maximum_workers = self.staffing_parameters[
            'maximum_workers'
        ]

        # A low-wage worker adds approximately $0.20 to the burn rate.
        projected_worker_burn_rate = burn_rate + 0.20
        worker_is_affordable = (
            current_profit > profit_threshold
            and revenue > costs
            and profit_per_worker > 0
            and average_revenue_per_step > projected_worker_burn_rate
            and recent_profit_change >= 0
        )

        # One manager supports layout relocation. Additional managers
        # would create unnecessary salary costs.
        projected_manager_burn_rate = burn_rate + 1.00
        manager_is_affordable = (
            current_profit > manager_threshold
            and average_revenue_per_step > projected_manager_burn_rate
        )

        if not has_manager and num_workers >= minimum_workers:
            if manager_is_affordable:
                return 3

        # Hire when demand is high and the additional wage is affordable.
        if (
            queue_pressure > hire_threshold
            and worker_is_affordable
            and num_workers < maximum_workers
        ):
            return 1

        # The environment fires the first idle employee. Only approve
        # firing when that employee is a worker, preserving the manager.
        idle_employees = [
            employee
            for employee in employees
            if getattr(employee.state, "name", "") == "IDLE"
        ]
        safe_worker_to_fire = (
            len(idle_employees) > 0
            and not getattr(
                idle_employees[0],
                "is_manager",
                False
            )
        )

        severe_overstaffing = queue_pressure < 0.75
        financial_pressure = (
            current_profit < 0
            or recent_profit_change < 0
        )

        if (
            queue_pressure < fire_threshold
            and num_workers > minimum_workers
            and safe_worker_to_fire
            and (financial_pressure or severe_overstaffing)
        ):
            return 2

        return 0

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

    def _get_naive_order_assignments(
        self,
        queue_info,
        employee_info
    ) -> list:
        """
        WEEK 2 STEP 2: Multi-objective worker-to-order assignment.

        Use the Hungarian algorithm to minimize total assignment cost
        while considering distance, order value, waiting time, and
        priority. Each idle worker receives at most one pending order.
        """

        assignments = [0] * 20

        idle_workers = self._get_idle_workers()
        indexed_orders = [
            (order_index, order)
            for order_index, order in enumerate(
                self.env.order_queue.orders[:20]
            )
            if order.status == "pending"
        ]

        if not idle_workers or not indexed_orders:
            return assignments

        orders = [order for _, order in indexed_orders]
        max_order_value = max(order.value for order in orders)

        benefit_matrix = np.zeros(
            (len(idle_workers), len(orders)),
            dtype=float
        )

        for worker_row, (_, worker_position) in enumerate(
            idle_workers
        ):
            for order_column, order in enumerate(orders):
                distance = self._calculate_order_distance(
                    worker_position,
                    order
                )
                distance_score = 1.0 / (1.0 + distance)
                value_score = order.value / max_order_value
                urgency_score = self._calculate_order_urgency(order)

                # Preserve the required 70/30 distance-value balance.
                base_benefit = (
                    0.70 * distance_score
                    + 0.30 * value_score
                )

                # Urgency increases the importance of the base score
                # without replacing distance and value objectives.
                total_benefit = base_benefit * (
                    1.0 + 0.25 * urgency_score
                )

                benefit_matrix[
                    worker_row,
                    order_column
                ] = total_benefit

        # linear_sum_assignment minimizes cost, so benefits are negated.
        worker_rows, order_columns = linear_sum_assignment(
            -benefit_matrix
        )

        for worker_row, order_column in zip(
            worker_rows,
            order_columns
        ):
            employee_index = idle_workers[worker_row][0]
            queue_index = indexed_orders[order_column][0]

            # The environment expects a one-based employee position.
            assignments[queue_index] = employee_index + 1

        return assignments

    def _get_idle_workers(self):
        """
        Return available non-manager workers and their positions.

        Each result contains the employee's zero-based position in the
        environment list and the worker's current warehouse position.
        """

        idle_workers = []

        for employee_index, employee in enumerate(
            self.env.employees
        ):
            is_idle = (
                getattr(employee.state, "name", "") == "IDLE"
            )
            has_no_order = (
                getattr(employee, "current_order_id", None) is None
            )
            is_manager = getattr(
                employee,
                "is_manager",
                False
            )

            if is_idle and has_no_order and not is_manager:
                idle_workers.append(
                    (employee_index, employee.position)
                )

        return idle_workers

    def _calculate_order_distance(self, worker_position, order):
        """
        Calculate the minimum Manhattan distance from a worker to any
        product required by an order.
        """

        grid = self.env.warehouse_grid
        minimum_distance = float("inf")

        for item_type in order.items:
            item_locations = grid.find_item_locations(item_type)

            for item_position in item_locations:
                distance = grid.manhattan_distance(
                    worker_position,
                    item_position
                )
                minimum_distance = min(
                    minimum_distance,
                    distance
                )

        if minimum_distance == float("inf"):
            return grid.width + grid.height

        return minimum_distance

    def _calculate_order_urgency(self, order):
        """
        Calculate urgency from waiting time, priority, and any express
        deadline. The returned score is between zero and one.
        """

        current_timestep = int(self.env.current_timestep)
        waiting_time = max(
            0,
            current_timestep - order.arrival_time
        )
        waiting_score = min(waiting_time / 300.0, 1.0)

        priority_scores = {
            "normal": 0.0,
            "priority": 0.5,
            "express": 1.0
        }
        priority_score = priority_scores.get(
            order.priority,
            0.0
        )

        deadline_score = 0.0
        if order.deadline is not None:
            time_remaining = max(
                0,
                order.deadline - current_timestep
            )
            deadline_score = 1.0 - min(
                time_remaining / 300.0,
                1.0
            )

        return max(
            waiting_score,
            priority_score,
            deadline_score
        )
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