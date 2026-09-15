import random
import math
from entities import Gatherer
from config import *

class GeneticAlgorithm:
    def __init__(self):
        self.generation = 1
        self.fitness_history = []
        self.trait_history = []  # Track trait averages over generations
    
    def create_initial_population(self):
        population = []
        for _ in range(INITIAL_POPULATION):
            gatherer = Gatherer()
            population.append(gatherer)
        return population
    
    def evaluate_fitness(self, population):
        fitness_scores = []
        for gatherer in population:
            fitness = gatherer.calculate_fitness()
            fitness_scores.append((gatherer, fitness))
        
        # Sort by fitness (highest first)
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        return fitness_scores
    
    def select_survivors(self, fitness_scores):
        """Choose strong parents while keeping genetic variety."""

        if not fitness_scores:
            return []

        population_size = len(fitness_scores)

        # Keep 25% as parents, creating useful selection pressure.
        survival_count = min(
            population_size,
            max(2, int(population_size * 0.25))
        )

        # Always save the best 5% so strong solutions are not lost.
        elite_count = min(
            survival_count,
            max(1, int(population_size * 0.05))
        )

        survivors = [
            gatherer
            for gatherer, fitness in fitness_scores[:elite_count]
        ]

        available = list(fitness_scores[elite_count:])

        min_fitness = fitness_scores[-1][1]
        max_fitness = fitness_scores[0][1]
        fitness_range = max(max_fitness - min_fitness, 0.000000001)

        def diversity_score(candidate):
            """Measure how different a candidate is from current survivors."""

            if not survivors:
                return 1.0

            nearest_distance = 1.0

            for survivor in survivors:
                differences = []

                for gene_name, value in candidate.genes.items():
                    min_val, max_val = GENE_RANGES[gene_name]
                    gene_range = max_val - min_val

                    difference = abs(
                        value - survivor.genes[gene_name]
                    ) / gene_range

                    differences.append(difference)

                average_difference = sum(differences) / len(differences)
                nearest_distance = min(
                    nearest_distance,
                    average_difference
                )

            return nearest_distance

        # Reserve one place for a randomly selected wildcard.
        wildcard_slots = 1 if survival_count - elite_count > 2 else 0
        tournament_slots = survival_count - elite_count - wildcard_slots

        for _ in range(tournament_slots):
            tournament_size = min(5, len(available))
            competitors = random.sample(available, tournament_size)

            def competitive_score(entry):
                gatherer, fitness = entry

                normalized_fitness = (
                    fitness - min_fitness
                ) / fitness_range

                return (
                    0.85 * normalized_fitness
                    + 0.15 * diversity_score(gatherer)
                )

            winner = max(competitors, key=competitive_score)
            survivors.append(winner[0])
            available.remove(winner)

        # The wildcard preserves a strategy that could become useful later.
        if wildcard_slots and available:
            survivors.append(random.choice(available)[0])

        return survivors
    
    def crossover(self, parent1, parent2):
        child_genes = {}
        for gene_name in parent1.genes:
            # 50% chance to inherit from each parent
            if random.random() < 0.5:
                child_genes[gene_name] = parent1.genes[gene_name]
            else:
                child_genes[gene_name] = parent2.genes[gene_name]
        
        child = Gatherer(genes=child_genes)
        return child
    
    def mutate(self, gatherer):
        """Mutate genes while balancing exploration and fine-tuning."""

        # Make larger changes early, then protect good solutions later.
        progress = min(max((self.generation - 1) / 29.0, 0.0), 1.0)
        mutation_rate = MUTATION_RATE * (1.0 - 0.50 * progress)
        mutation_strength = MUTATION_STRENGTH * (1.0 - 0.75 * progress)

        # Increase mutation if average fitness has stopped improving.
        if len(self.fitness_history) >= 5:
            recent = [
                entry["avg_fitness"]
                for entry in self.fitness_history[-5:]
            ]

            if max(recent) - min(recent) < 0.05:
                mutation_rate = min(0.20, mutation_rate * 1.50)
                mutation_strength = min(0.30, mutation_strength * 1.25)

        # Each trait needs a different mutation size.
        gene_scales = {
            "speed": 0.55,
            "caution": 0.80,
            "search_pattern": 0.65,
            "efficiency": 0.45,
            "cooperation": 0.60
        }

        for gene_name, current_value in gatherer.genes.items():
            if random.random() < mutation_rate:
                min_val, max_val = GENE_RANGES[gene_name]
                gene_range = max_val - min_val
                sigma = gene_range * mutation_strength * gene_scales[gene_name]

                # Most mutations are small, but some can be larger.
                new_value = current_value + random.gauss(0.0, sigma)

                # Reflect values back inside their allowed range.
                while new_value < min_val or new_value > max_val:
                    if new_value < min_val:
                        new_value = min_val + (min_val - new_value)

                    if new_value > max_val:
                        new_value = max_val - (new_value - max_val)

                gatherer.genes[gene_name] = new_value

        # A rare reset helps the population escape a local optimum.
        if random.random() < mutation_rate * 0.10:
            gene_name = random.choice(list(gatherer.genes.keys()))
            min_val, max_val = GENE_RANGES[gene_name]
            gatherer.genes[gene_name] = random.uniform(min_val, max_val)
    
    def create_next_generation(self, population):
        # Evaluate fitness
        fitness_scores = self.evaluate_fitness(population)
        
        # Record statistics
        if fitness_scores:
            best_fitness = fitness_scores[0][1]
            avg_fitness = sum(fitness for _, fitness in fitness_scores) / len(fitness_scores)
            self.fitness_history.append({
                'generation': self.generation,
                'best_fitness': best_fitness,
                'avg_fitness': avg_fitness
            })
            
            print(
                f"Generation {self.generation}: "
                f"average fitness = {avg_fitness:.2f}, "
                f"best fitness = {best_fitness:.2f}"
            )
            
            # Record trait averages
            all_gatherers = [gatherer for gatherer, _ in fitness_scores]
            trait_averages = {
                'generation': self.generation,
                'avg_speed': sum(g.genes['speed'] for g in all_gatherers) / len(all_gatherers),
                'avg_caution': sum(g.genes['caution'] for g in all_gatherers) / len(all_gatherers),
                'avg_search_pattern': sum(g.genes['search_pattern'] for g in all_gatherers) / len(all_gatherers),
                'avg_efficiency': sum(g.genes['efficiency'] for g in all_gatherers) / len(all_gatherers),
                'avg_cooperation': sum(g.genes['cooperation'] for g in all_gatherers) / len(all_gatherers)
            }
            self.trait_history.append(trait_averages)
        
        # Select survivors
        survivors = self.select_survivors(fitness_scores)
        
        # Create new population
        new_population = []
        
        # Add survivors (reset their state)
        for survivor in survivors:
            new_gatherer = Gatherer(genes=survivor.genes)
            new_population.append(new_gatherer)
        
        # Create offspring to fill remaining slots
        offspring_count = INITIAL_POPULATION - len(survivors)
        for _ in range(offspring_count):
            parent1 = random.choice(survivors)
            parent2 = random.choice(survivors)
            child = self.crossover(parent1, parent2)
            self.mutate(child)
            new_population.append(child)
        
        self.generation += 1
        return new_population
    
    def get_population_stats(self, population):
        if not population:
            return {
                'alive_count': 0,
                'total_count': 0,
                'avg_fitness': 0,
                'best_fitness': 0,
                'avg_speed': 0,
                'avg_caution': 0,
                'avg_cooperation': 0
            }
        
        alive_gatherers = [g for g in population if g.alive]
        alive_count = len(alive_gatherers)
        total_count = len(population)
        
        if alive_gatherers:
            fitness_scores = [g.calculate_fitness() for g in alive_gatherers]
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            best_fitness = max(fitness_scores)
            avg_speed = sum(g.genes['speed'] for g in alive_gatherers) / len(alive_gatherers)
            avg_caution = sum(g.genes['caution'] for g in alive_gatherers) / len(alive_gatherers)
            avg_cooperation = sum(g.genes['cooperation'] for g in alive_gatherers) / len(alive_gatherers)
        else:
            # Check all gatherers if none alive
            fitness_scores = [g.calculate_fitness() for g in population]
            avg_fitness = sum(fitness_scores) / len(fitness_scores) if fitness_scores else 0
            best_fitness = max(fitness_scores) if fitness_scores else 0
            avg_speed = sum(g.genes['speed'] for g in population) / len(population)
            avg_caution = sum(g.genes['caution'] for g in population) / len(population)
            avg_cooperation = sum(g.genes['cooperation'] for g in population) / len(population)
        
        return {
            'alive_count': alive_count,
            'total_count': total_count,
            'avg_fitness': avg_fitness,
            'best_fitness': best_fitness,
            'avg_speed': avg_speed,
            'avg_caution': avg_caution,
            'avg_cooperation': avg_cooperation
        }
    
    def reset(self):
        self.generation = 1
        self.fitness_history = []
        self.trait_history = []