#!/usr/bin/env python3
"""
Improved name generator with better organization.
"""

import random
from typing import Tuple, Set

from exceptions import UserCreationError

class NameGenerator:
    """Generates unique names from Lord of the Rings and War and Peace characters."""
    
    # Class constants - more organized and documented
    LOTR_FIRST_NAMES = [
        "Aragorn", "Gandalf", "Frodo", "Samwise", "Pippin", "Merry", "Legolas",
        "Gimli", "Boromir", "Faramir", "Eowyn", "Arwen", "Galadriel", "Elrond",
        "Thranduil", "Bilbo", "Thorin", "Balin", "Dwalin", "Fili", "Kili",
        "Gloin", "Oin", "Ori", "Dori", "Nori", "Bifur", "Bofur", "Bombur",
        "Smaug", "Gollum", "Saruman", "Grima", "Theoden", "Eomer", "Haldir"
    ]
    
    WAR_AND_PEACE_FIRST_NAMES = [
        "Pierre", "Andrei", "Natasha", "Marya", "Nikolai", "Sonya", "Anatole",
        "Helene", "Vasily", "Anna", "Boris", "Dolokhov", "Kutuzov", "Bagration",
        "Denisov", "Rostov", "Kutuzov", "Napoleon", "Alexander", "Mikhail",
        "Vera", "Liza", "Petya", "Ilya", "Agafya", "Praskovya", "Dmitri",
        "Fyodor", "Ivan", "Sergei", "Vladimir", "Konstantin", "Pavel"
    ]
    
    LOTR_LAST_NAMES = [
        "Baggins", "Took", "Brandybuck", "Gamgee", "Strider", "Greyhame",
        "Greenleaf", "Oakenshield", "Ironfoot", "SonofThrain", "SonofGloin",
        "Evenstar", "Rivendell", "Lorien", "Mirkwood", "Gondor", "Rohan",
        "Rivendell", "Shire", "Mordor", "Isengard", "Helms", "Deep",
        "Woodland", "Erebor", "Moria", "Laketown", "Esgaroth", "Dale"
    ]
    
    WAR_AND_PEACE_LAST_NAMES = [
        "Bezukhov", "Bolkonsky", "Rostov", "Kuragin", "Drubetskoy", "Karagin",
        "Mamonov", "Berg", "Dolokhov", "Zherkov", "Denisov", "Kutuzov",
        "Bagration", "Napoleon", "Alexander", "Smirnov", "Ivanov", "Petrov",
        "Sokolov", "Popov", "Volkov", "Novikov", "Fedorov", "Morozov",
        "Volkov", "Alekseev", "Lebedev", "Semenov", "Egorov", "Pavlov",
        "Kozlov", "Stepanov", "Nikolaev", "Orlov", "Andreev", "Makarov",
        "Nikitin", "Zakharov", "Zaitsev", "Solovyov", "Borisov", "Yakovlev"
    ]
    
    # Constants
    MAX_ATTEMPTS = 1000
    
    def __init__(self):
        self.used_names: Set[str] = set()
    
    def generate_unique_name(self) -> Tuple[str, str]:
        """Generate a unique first and last name combination."""
        for _ in range(self.MAX_ATTEMPTS):
            first_name, last_name = self._generate_random_name()
            name_combination = f"{first_name} {last_name}"
            
            if name_combination not in self.used_names:
                self.used_names.add(name_combination)
                return first_name, last_name
        
        raise UserCreationError("Unable to generate unique name combination")
    
    def _generate_random_name(self) -> Tuple[str, str]:
        """Generate a random name from available sources."""
        use_lotr = random.choice([True, False])
        
        if use_lotr:
            first_name = random.choice(self.LOTR_FIRST_NAMES)
            last_name = random.choice(self.LOTR_LAST_NAMES)
        else:
            first_name = random.choice(self.WAR_AND_PEACE_FIRST_NAMES)
            last_name = random.choice(self.WAR_AND_PEACE_LAST_NAMES)
        
        return first_name, last_name
