from typing import List, Optional, TypedDict


class ParliamentQuestion(TypedDict):
    """
    Represents a question asked in the Parliament.

    Attributes:
        quesNo: Unique identifier for the question
        subjects: Topic or subject of the question
        lokNo: Lok Sabha session number
        member: List of members who asked the question
        ministry: Ministry to which question is directed
        type: Type of question (STARRED/UNSTARRED)
        date: Date of the question
        questionsFilePathLocal: Local path to question PDF
        questionsFilePathWeb: Web URL of question PDF
        questionsFilePathHindiLocal: Optional local path to Hindi version
        questionsFilePathHindiWeb: Optional web URL of Hindi version
        questionText: Optional extracted question text
        answerText: Optional extracted answer text
        sessionNo: Optional parliament session number
    """

    quesNo: int
    subjects: str
    lokNo: str
    member: List[str]
    ministry: str
    type: str
    date: str
    questionsFilePathLocal: str
    questionsFilePathWeb: str
    questionsFilePathHindiLocal: Optional[str]
    questionsFilePathHindiWeb: Optional[str]
    questionText: Optional[str]
    answerText: Optional[str]
    sessionNo: Optional[str]
