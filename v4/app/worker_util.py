import random


def crossover_with_fittest(bot, bots, total_fitness):
    parent_a_index = weighted_selection(bots, total_fitness)
    parent_b_index = weighted_selection(bots, total_fitness)

    parent_a = bots[parent_a_index]
    parent_b = bots[parent_b_index]

    # Crossover the two parents to produce a new child brain
    bot.crossover(parent_a, parent_b)
    return parent_a_index, parent_b_index


def weighted_selection(bots, total_fitness):
    index = 0
    start = random.uniform(0, 1)

    while start > 0:
        normalised_fitness = bots[index].fitness / total_fitness
        start -= normalised_fitness
        index += 1

    index -= 1  # Adjust index because we incremented it at the end of the loop

    return index
