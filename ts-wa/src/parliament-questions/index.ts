import path from 'path';
import fs from 'fs';
import { groupBy } from 'lodash';

import { StepStatus } from '../pipeline/pipeline';
import { findProjectRoot, kebabCaseNames, filenameGenerator } from '../file-utils/project-root';
import { downloadPDFs } from '../file-utils/fetch-pdf-from-url';

export interface ParliamentQuestion {
  quesNo: number;
  subjects: string;
  lokNo: string;
  member: string[];
  ministry: string;
  type: string;
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
  const { sansad, session } = outputs;

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad-${sansad}/${session}`);
  const qnaFile = path.join(sansadSessionDirectory, `${sansad}_${session}.qna.json`);
  const qnaData = require(qnaFile);

  const groupByMinistries = groupBy(qnaData.listOfQuestions, 'ministry');

  const failedSansadSessionQuestionDownload: string[] = [];
  const downloadedSansadSessionQuestions: ParliamentQuestion[] = [];

  for (const ministry in groupByMinistries) {
    for (const question of groupByMinistries[ministry]) {
      const { quesNo, subjects, lokNo, member, ministry, type, date, questionsFilePath, questionsFilePathHindi } =
        question;

      const ministryDirectory = path.join(sansadSessionDirectory, 'ministries', `./${kebabCaseNames(ministry)}`);
      const questionDirectory = path.join(ministryDirectory, kebabCaseNames(question.quesNo.toString().trim()));
      const projectRoot = await findProjectRoot();

      if (!fs.existsSync(questionDirectory)) {
        fs.mkdirSync(questionDirectory, { recursive: true });
      }

      const pdfUrl = questionsFilePath;
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
          quesNo,
          subjects,
          lokNo,
          member,
          ministry,
          type,
          date,
          questionsFilePathWeb: questionsFilePath,
          questionsFilePathLocal: `${relativequestionDirectory}/${filenameGenerator(pdfUrl, 0)}`,
          questionsFilePathHindiWeb: questionsFilePathHindi,
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
