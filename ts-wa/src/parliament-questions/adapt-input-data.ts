import path from 'path';
import { ParliamentQuestion } from '.';
import { StepStatus } from '../pipeline/pipeline';

interface SourceParliamentQuestion {
  quesNo: number;
  subjects: string;
  lokNo: string;
  member: string[];
  ministry: string;
  type: 'STARRED' | 'UNSTARRED';
  date: string;
  questionText: string | null;
  answerText: string | null;
  answerTextHindi: string | null;
  questionsFilePath: string;
  questionsFilePathHindi: string;
  sessionNo: string;
  supplementaryQuestionResDtoList?: any[];
  supplementaryType?: boolean;
}

export async function adaptSourceQuestionsListToParliamentQuestions(
  outputs: Record<string, any>
): Promise<{ parliamentSessionQuestions: ParliamentQuestion[]; status: StepStatus }> {
  const { sansad, session } = outputs;

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad-${sansad}/${session}`);
  const qnaFile = path.join(sansadSessionDirectory, `${sansad}_${session}.qna.source.json`);
  let qnaData = require(qnaFile);

  const sourceQuestionsList: SourceParliamentQuestion[] = qnaData[0].listOfQuestions;

  const parliamentSessionQuestions: ParliamentQuestion[] = sourceQuestionsList.map(
    (question: SourceParliamentQuestion) => ({
      questionNumber: question.quesNo,
      subjects: question.subjects,
      loksabhaNumber: question.lokNo,
      sessionNumber: question.sessionNo,
      member: question.member,
      ministry: question.ministry,
      type: question.type,
      date: question.date,
      questionsFilePathLocal: question.questionsFilePath,
      questionsFilePathWeb: question.questionsFilePath,
      questionsFilePathHindiLocal: question.questionsFilePathHindi,
      questionsFilePathHindiWeb: question.questionsFilePathHindi,
    })
  );

  return {
    parliamentSessionQuestions,
    status: 'SUCCESS',
  };
}
