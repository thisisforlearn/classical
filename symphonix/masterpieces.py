"""Masterpieces registry + random-piece selector.

`MASTERPIECES[key][0]` is that composer's signature showpiece (max mode);
the whole list is the random pool (random mode).
"""
import random

MASTERPIECES = {
    "bach": [
        "Toccata and Fugue in D minor BWV 565",
        "Brandenburg Concerto No. 3",
        "Air on the G String",
        "Goldberg Variations",
        "Well-Tempered Clavier Book 1 Prelude 1",
        "Cello Suite No. 1 Prelude",
        "Mass in B Minor Kyrie",
    ],
    "mozart": [
        "Symphony No. 41 Jupiter",
        "The Marriage of Figaro Overture",
        "Requiem Mass Lacrimosa",
        "Eine kleine Nachtmusik",
        "Piano Concerto No. 21 Andante",
        "Don Giovanni Overture",
        "Rondo alla Turca",
    ],
    "beethoven": [
        "Symphony No. 5",
        "Symphony No. 9 Ode to Joy",
        "Moonlight Sonata",
        "Fur Elise",
        "Symphony No. 7",
        "Egmont Overture",
        "Emperor Concerto",
    ],
    "chopin": [
        "Nocturne Op. 9 No. 2",
        "Heroic Polonaise Op. 53",
        "Minute Waltz",
        "Fantaisie-Impromptu",
        "Ballade No. 1",
        "Prelude Op. 28 No. 4",
        "Etude Op. 10 No. 3",
    ],
    "schubert": [
        "Trout Quintet",
        "Ave Maria",
        "Unfinished Symphony",
        "Impromptu Op. 90 No. 3",
        "Piano Sonata in A minor",
    ],
    "brahms": [
        "Hungarian Dance No. 5",
        "Symphony No. 4",
        "Brahms Lullaby",
        "Piano Concerto No. 2",
        "Academic Festival Overture",
    ],
    "vivaldi": [
        "Four Seasons Spring",
        "Four Seasons Winter",
        "Gloria",
        "Four Seasons Summer",
    ],
    "tchaikovsky": [
        "Swan Lake",
        "Nutcracker Suite",
        "1812 Overture",
        "Piano Concerto No. 1",
        "Pathetique Symphony",
        "Sleeping Beauty Waltz",
    ],
    "handel": [
        "Messiah Hallelujah Chorus",
        "Water Music",
        "Music for the Royal Fireworks",
        "Zadok the Priest",
    ],
    "haydn": [
        "Surprise Symphony",
        "Trumpet Concerto",
        "Emperor Hymn",
        "Farewell Symphony",
    ],
    "wagner": [
        "Ride of the Valkyries",
        "Bridal Chorus",
        "Prelude to Tristan and Isolde",
        "Tannhauser Overture",
    ],
    "liszt": [
        "Hungarian Rhapsody No. 2",
        "Liebestraum No. 3",
        "La Campanella",
        "Un Sospiro",
    ],
    "debussy": [
        "Clair de Lune",
        "La Mer",
        "Arabesque No. 1",
        "Prelude to the Afternoon of a Faun",
    ],
    "grieg": [
        "In the Hall of the Mountain King",
        "Morning Mood",
        "Piano Concerto in A minor",
    ],
    "rachmaninoff": [
        "Piano Concerto No. 2",
        "Rhapsody on a Theme of Paganini",
        "Prelude in C Sharp Minor",
        "Vocalise",
    ],
    "satie": [
        "Gymnopedie No. 1",
        "Gnossienne No. 1",
        "Je te veux",
    ],
    "schumann": [
        "Traumerei",
        "Carnaval Carnival",
        "Symphony No. 3 Rhenish",
    ],
    "mendelssohn": [
        "Wedding March Midsummer",
        "Hebrides Overture",
        "Spring Song",
    ],
    "verdi": [
        "La Donna e Mobile",
        "Va Pensiero",
        "Libiamo from La Traviata",
    ],
    "puccini": [
        "Nessun Dorma",
        "O Mio Babbino Caro",
        "Un Bel Di Vedremo",
    ],
    "scarlatti": [
        "Sonata in D minor K. 141",
        "Keyboard Sonata K. 27",
        "Keyboard Sonata K. 555",
    ],
    "dvorak": [
        "New World Symphony",
        "Slavonic Dance No. 2",
        "Humoresque No. 7",
        "Cello Concerto Finale",
    ],
    "mahler": [
        "Symphony No. 5 Adagietto",
        "Symphony No. 2 Resurrection",
        "Symphony No. 9",
    ],
    "stravinsky": [
        "The Rite of Spring",
        "The Firebird",
        "Petrushka",
    ],
}


def random_composer(exclude=None):
    pool = [k for k in MASTERPIECES if k != exclude]
    return random.choice(pool)


def random_piece(composer_key=None):
    """Returns (composer_key, famous work string)."""
    key = composer_key or random_composer()
    works = MASTERPIECES.get(key, [])
    if not works:
        return key, ""
    return key, random.choice(works)


def signature_piece(composer_key):
    """The single most famous showpiece of a composer (max mode)."""
    works = MASTERPIECES.get(composer_key, [])
    return works[0] if works else ""


# Globally recommended cornerstones (menu "Recommended" wheel)
RECOMMENDED = [
    ("mozart", "Symphony No. 41 Jupiter", "Mozart Jupiter symphony 41"),
    ("mozart", "The Marriage of Figaro Overture", "Mozart Figaro overture"),
    ("mozart", "Requiem Mass Lacrimosa", "Mozart Requiem lacrimosa"),
    ("mozart", "Eine kleine Nachtmusik", "Mozart Eine kleine Nachtmusik"),
    ("mozart", "Piano Concerto No. 21 Andante", "Mozart concerto 21 andante"),
    ("mozart", "Don Giovanni Overture", "Mozart Don Giovanni overture"),
    ("beethoven", "Symphony No. 5", "Beethoven symphony 5"),
    ("beethoven", "Symphony No. 9 Ode to Joy", "Beethoven symphony 9"),
    ("vivaldi", "Four Seasons Spring", "Vivaldi Spring four seasons"),
    ("bach", "Toccata and Fugue in D minor BWV 565", "Bach toccata fugue"),
    ("handel", "Messiah Hallelujah Chorus", "Handel hallelujah chorus"),
    ("grieg", "In the Hall of the Mountain King", "Grieg mountain king"),
]
