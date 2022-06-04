import csv
import itertools
import sys

PROBS = {
 
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {
 
        2: {
            True: 0.65,
            False: 0.35
        },
 
        1: {
            True: 0.56,
            False: 0.44
        },
 
        0: {
            True: 0.01,
            False: 0.99
        }
    },
 
    "mutation": 0.01
}


def main():
 
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])
 
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }
 
    names = set(people)
    for have_trait in powerset(names):
 
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue
 
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):
 
                p = JointProbability(people, one_gene, two_genes, have_trait)
                Update(probabilities, one_gene, two_genes, have_trait, p)
 
    Normalize(probabilities)
 
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename): 
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s): 
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def JointProbability(people, one_gene, two_genes, have_trait): 

    joint_prob = 1

    for person in people:

        person_prob = 1
        person_genes = (2 if person in two_genes else 1 if person in one_gene else 0)
        person_trait = person in have_trait

        mother = people[person]['mother']
        father = people[person]['father']

        if not mother and not father:
            person_prob *= PROBS['gene'][person_genes]
        else:
            if mother in two_genes:
                mother_prob = 1 - PROBS['mutation']
            elif mother in one_gene:
                mother_prob = 0.5
            else:
                mother_prob = PROBS['mutation']
            if father in two_genes:
                father_prob = 1 - PROBS['mutation']
            elif mother in one_gene:
                father_prob = 0.5
            else:
                father_prob = PROBS['mutation']

            if person_genes == 2:
                person_prob *= mother_prob * father_prob
            elif person_genes == 1:
                person_prob *= (1 - mother_prob) * father_prob + (1 - father_prob) * mother_prob
            else:
                person_prob *= (1 - mother_prob) * (1 - father_prob)

        person_prob *= PROBS['trait'][person_genes][person_trait]
        joint_prob *= person_prob

    return joint_prob


def Update(probabilities, one_gene, two_genes, have_trait, p): 

    for person in probabilities:
        person_genes = (2 if person in two_genes else 1 if person in one_gene else 0)
        person_trait = person in have_trait

        probabilities[person]['gene'][person_genes] += p
        probabilities[person]['trait'][person_trait] += p


def Normalize(probabilities): 

    for person in probabilities:
        gene_prob_sum = sum(probabilities[person]['gene'].values())
        trait_prob_sum = sum(probabilities[person]['trait'].values())

        probabilities[person]['gene'] = {genes: (prob / gene_prob_sum) for genes, prob in
                                         probabilities[person]['gene'].items()}
        probabilities[person]['trait'] = {trait: (prob / trait_prob_sum) for trait, prob in
                                          probabilities[person]['trait'].items()}


if __name__ == "__main__":
    main()
