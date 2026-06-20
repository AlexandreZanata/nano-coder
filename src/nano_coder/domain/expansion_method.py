from enum import StrEnum


class ExpansionMethod(StrEnum):
    SELF_INSTRUCT = "selfInstruct"
    EVOL_DEEPEN = "evolDeepen"
    EVOL_WIDEN = "evolWiden"
    EVOL_SHORTEN = "evolShorten"
