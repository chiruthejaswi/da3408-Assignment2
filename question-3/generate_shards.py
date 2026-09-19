"""
Generates 8 synthetic CSV shards of user signup records, each with a known,
seeded number of deliberately invalid rows (malformed email address or a
missing required field: name, email, or signup_date).

Deterministic: re-running this script produces byte-identical shards, so the
"known, seeded number of invalid rows per shard" can be checked against the
validator's output.
"""
import csv
import random

REQUIRED_FIELDS = ["name", "email", "signup_date"]
NUM_SHARDS = 8
ROWS_PER_SHARD = 120

FIRST_NAMES = ["Alice", "Bob", "Chen", "Diego", "Emma", "Farah", "Grace", "Hiro",
               "Ines", "Jamal", "Kira", "Liam", "Maya", "Noor", "Omar", "Priya"]
LAST_NAMES = ["Smith", "Nguyen", "Garcia", "Patel", "Kim", "Rossi", "Diallo",
              "Muller", "Andersen", "Silva"]
DOMAINS = ["example.com", "mail.co", "corp.io", "webhost.net"]

# Deliberately malformed email patterns (missing @, missing domain, stray spaces, etc.)
BAD_EMAIL_PATTERNS = [
    lambda local: f"{local}example.com",       # missing @
    lambda local: f"{local}@",                 # missing domain
    lambda local: f"@example.com",              # missing local part
    lambda local: f"{local}@@example.com",      # double @
    lambda local: f" {local}@example.com",      # leading whitespace
    lambda local: f"{local}@example",           # missing TLD
]


def make_row(rng, row_id, force_invalid_kind=None):
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    local = f"{first.lower()}.{last.lower()}{row_id}"
    domain = rng.choice(DOMAINS)
    good_email = f"{local}@{domain}"
    name = f"{first} {last}"
    date = f"2026-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"

    row = {"name": name, "email": good_email, "signup_date": date}

    if force_invalid_kind == "bad_email":
        row["email"] = rng.choice(BAD_EMAIL_PATTERNS)(local)
    elif force_invalid_kind == "missing_field":
        missing = rng.choice(REQUIRED_FIELDS)
        row[missing] = ""

    return row


def generate_shard(shard_index, seed, n_invalid):
    rng = random.Random(seed)
    n_valid = ROWS_PER_SHARD - n_invalid

    kinds = (["bad_email"] * ((n_invalid + 1) // 2) +
             ["missing_field"] * (n_invalid // 2))
    rng.shuffle(kinds)

    rows = []
    for i in range(n_valid):
        rows.append(make_row(rng, row_id=f"{shard_index}_{i}"))
    for i, kind in enumerate(kinds):
        rows.append(make_row(rng, row_id=f"{shard_index}_bad{i}", force_invalid_kind=kind))

    rng.shuffle(rows)
    return rows


def main():
    # A different, but deterministic, seeded invalid-row count per shard —
    # known ahead of time so the validator's reported count can be checked.
    invalid_counts = [5, 9, 3, 14, 7, 11, 2, 8]  # sums to 59 across 8 shards
    assert len(invalid_counts) == NUM_SHARDS

    print(f"{'shard':>7} {'seed':>6} {'invalid_rows':>13} {'total_rows':>11}")
    for shard_index in range(NUM_SHARDS):
        seed = 1000 + shard_index
        n_invalid = invalid_counts[shard_index]
        rows = generate_shard(shard_index, seed, n_invalid)

        path = f"shards/shard_{shard_index}.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        print(f"{shard_index:>7} {seed:>6} {n_invalid:>13} {len(rows):>11}")

    print(f"\nTotal invalid rows across all shards (ground truth): {sum(invalid_counts)}")


if __name__ == "__main__":
    main()
