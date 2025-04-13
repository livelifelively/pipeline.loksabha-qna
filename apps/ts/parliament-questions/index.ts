import path from 'path';
import fs from 'fs';
import { groupBy } from 'lodash';

import { StepStatus } from '../pipeline/pipeline';
import { findProjectRoot, kebabCaseNames, filenameGenerator } from '../utils/project-root';
import { downloadPDFs } from '../utils/fetch-pdf-from-url';

export interface ParliamentQuestion {
  questionNumber: number;
  subjects: string;
  loksabhaNumber: string;
  member: string[];
  ministry: string;
  type: 'STARRED' | 'UNSTARRED';
  date: string;
  questionsFilePathLocal: string;
  questionsFilePathWeb: string;
  questionsFilePathHindiLocal?: string;
  questionsFilePathHindiWeb?: string;
  questionText?: string;
  answerText?: string;
  sessionNo?: string;
}

export async function fetchAndCategorizeQuestionsPdfs(outputs: Record<string, any>): Promise<{
  failedSansadSessionQuestionDownload: string[];
  downloadedSansadSessionQuestions: ParliamentQuestion[];
  status: StepStatus;
}> {
  const { parliamentSessionQuestions, sansad, session } = outputs;

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad/${sansad}/${session}`);

  const groupByMinistries = groupBy(parliamentSessionQuestions, 'ministry');

  const failedSansadSessionQuestionDownload: string[] = [];
  const downloadedSansadSessionQuestions: ParliamentQuestion[] = [];

  for (const ministry in groupByMinistries) {
    for (const question of groupByMinistries[ministry]) {
      const {
        questionNumber,
        subjects,
        loksabhaNumber,
        member,
        ministry,
        type,
        date,
        questionsFilePathWeb,
        questionsFilePathHindiWeb,
        questionsFilePathHindiLocal,
      } = question;

      const ministryDirectory = path.join(sansadSessionDirectory, 'ministries', `./${kebabCaseNames(ministry)}`);
      const questionDirectory = path.join(ministryDirectory, kebabCaseNames(question.questionNumber.toString().trim()));
      const projectRoot = await findProjectRoot();

      if (!fs.existsSync(questionDirectory)) {
        fs.mkdirSync(questionDirectory, { recursive: true });
      }

      const pdfUrl = questionsFilePathWeb;
      const relativequestionDirectory = path.relative(projectRoot, questionDirectory);

      try {
        await downloadPDFs([pdfUrl], {
          outputDirectory: questionDirectory,
          filenameGenerator,
          timeoutMs: 30000,
          retries: 5,
          retryDelayMs: 2000,
          overwriteExisting: false,
        });
        downloadedSansadSessionQuestions.push({
          questionNumber,
          subjects,
          loksabhaNumber,
          member,
          ministry,
          type,
          date,
          questionsFilePathWeb: questionsFilePathWeb,
          questionsFilePathLocal: `${relativequestionDirectory}/${filenameGenerator(pdfUrl, 0)}`,
          questionsFilePathHindiWeb: questionsFilePathHindiWeb,
          questionsFilePathHindiLocal: questionsFilePathHindiLocal,
        });
      } catch (error) {
        console.error('Error in downloading PDF: ', error);
        failedSansadSessionQuestionDownload.push(pdfUrl);
      }
    }
  }

  return {
    failedSansadSessionQuestionDownload,
    downloadedSansadSessionQuestions,
    status: failedSansadSessionQuestionDownload.length > 0 ? 'PARTIAL' : 'SUCCESS',
  };
}
