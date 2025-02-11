import path from 'path';
import fs from 'fs';

import { downloadPDFs } from '../file-utils/fetch-pdf-from-url';

import { groupBy } from 'lodash';
import { PipelineStep } from './pipeline';
import { runPipeline } from './pipeline';
import { findProjectRoot } from '../file-utils/project-root';

type StepStatus = 'SUCCESS' | 'FAILURE' | 'PARTIAL';

function kebabCase(name: string) {
  let smallerName = name.trim().split(',').join('').split('and').join('').split('&').join('');
  let kebabCaseString = smallerName.split(' ').join('-').toLowerCase();
  return kebabCaseString;
}

const filenameGenerator = (url: string, index: number) => {
  const parsedUrl = new URL(url);
  const basename = path.basename(parsedUrl.pathname);
  return basename.endsWith('.pdf') ? basename : `downloaded_file_${index}.pdf`;
};

interface ParliamentQuestion {
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

async function fetchAndCategorizeQuestionsPdfs(outputs: Record<string, any>): Promise<{
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

      const ministryDirectory = path.join(sansadSessionDirectory, 'ministries', `./${kebabCase(ministry)}`);
      const questionDirectory = path.join(ministryDirectory, kebabCase(question.quesNo.toString().trim()));
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

export async function sansadSessionPipeline(sansad: string, session: string): Promise<any> {
  console.log('SANSAD SESSION PROCESSING INITIALIZED: ', sansad, session);

  const steps: PipelineStep[] = [
    {
      name: 'Fetch Questions PDFs',
      function: fetchAndCategorizeQuestionsPdfs,
      key: 'FETCH_QUESTIONS_PDFS',
      input: {
        sansad: sansad,
        session: session,
      },
    },
  ];

  let outputs: Record<string, any> = {
    sansad: sansad,
    session: session,
    failedSansadSessionQuestionDownload: [],
    downloadedSansadSessionQuestions: [],
  };

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad-${sansad}/${session}`);
  const sansadProgressDir = path.join(sansadSessionDirectory, 'sansad-session-pipeline-logs');
  const progressStatusFile = path.join(sansadProgressDir, 'progress-status.json');

  try {
    const lastStepOutput = await runPipeline(steps, outputs, sansadProgressDir, progressStatusFile);
    return lastStepOutput;
  } catch (error) {
    console.error('Error in processing: ', error);
  }
}
