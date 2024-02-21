import os
from dataclasses import dataclass


@dataclass
class Directories:
    token_database:str  =os.path.join(os.getcwd(),'token_database')
    support:str         =os.path.join(os.getcwd(),'support')
    token_pairs:str     =os.path.join(os.getcwd(),'support','token_pairs.xlsx')
    dataset_updates:str =os.path.join(os.getcwd(),'support','dataset_updates.pkl')
