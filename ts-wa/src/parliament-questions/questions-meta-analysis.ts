import path from 'path';
import fs from 'fs';
import { groupBy } from 'lodash';

import { ProgressIteration, StepStatus } from '../pipeline/pipeline';
import { findProjectRoot, kebabCaseNames, filenameGenerator } from '../utils/project-root';
import { downloadPDFs } from '../utils/fetch-pdf-from-url';
import { successfulStepDataFilePath } from '../utils/pipeline-utils';
import { ParliamentQuestion } from '.';

export async function fetchMetaAnalysisForQuestionsPdfs(outputs: Record<string, any>): Promise<any> {
  const { sansad, session } = outputs;

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad-${sansad}/${session}`);
  const fetchedQnAPdfProgressStatusFilePath = path.join(
    sansadSessionDirectory,
    'sansad-session-pipeline-logs/progress-status.json'
  );
  const fetchedQnAPdfProgressStatus = require(fetchedQnAPdfProgressStatusFilePath);

  console.log(JSON.stringify(fetchedQnAPdfProgressStatus));

  const fetchedQnAPdfDataFilePath = successfulStepDataFilePath(fetchedQnAPdfProgressStatus, 1);

  if (!fetchedQnAPdfDataFilePath) {
    throw new Error("Step's Successfull status data file not found");
  }

  const absolutePath = path.join(findProjectRoot(), fetchedQnAPdfDataFilePath);
  const fetchedQnAPdfData = require(absolutePath);

  let baseData = fetchedQnAPdfData.data.downloadedSansadSessionQuestions.map(
    (val: ParliamentQuestion): ParliamentQuestion => {
      return {
        quesNo: val.quesNo,
        subjects: val.subjects.trim(),
        lokNo: val.lokNo.trim(),
        member: val.member.map((m) => m.trim()),
        ministry: val.ministry.trim(),
        type: val.type.trim(),
        date: val.date.trim(),
        questionsFilePathLocal: val.questionsFilePathLocal.trim(),
        questionsFilePathWeb: val.questionsFilePathWeb.trim(),
        questionsFilePathHindiLocal: val.questionsFilePathHindiLocal?.trim(),
        questionsFilePathHindiWeb: val.questionsFilePathHindiWeb?.trim(),
        questionText: val.questionText?.trim(),
        answerText: val.answerText?.trim(),
        sessionNo: val.sessionNo?.trim(),
      };
    }
  );

  console.log(JSON.stringify(baseData));

  // #TODO
  // number of pages
  // has table
  // number of characters in the answer
  // question text
  // answer text
  // structure conformance

  // input question
  // output meta analysis on the document

  // used to filter questions -
  // 1. those with tables = high priority
  // 2. fewer answer characters or fewer pages = low priority

  //   console.log(successfulStepFilePath(fetchedQnAPdfProgressStatus, 1));

  //   const groupByMinistries = groupBy(qnaData.listOfQuestions, 'ministry');

  //   const failedSansadSessionQuestionDownload: string[] = [];
  //   const downloadedSansadSessionQuestions: ParliamentQuestion[] = [];

  //   for (const ministry in groupByMinistries) {
  //     for (const question of groupByMinistries[ministry]) {
  //       const { quesNo, subjects, lokNo, member, ministry, type, date, questionsFilePath, questionsFilePathHindi } =
  //         question;

  //       const ministryDirectory = path.join(sansadSessionDirectory, 'ministries', `./${kebabCaseNames(ministry)}`);
  //       const questionDirectory = path.join(ministryDirectory, kebabCaseNames(question.quesNo.toString().trim()));
  //       const projectRoot = await findProjectRoot();

  //       if (!fs.existsSync(questionDirectory)) {
  //         fs.mkdirSync(questionDirectory, { recursive: true });
  //       }

  //       const pdfUrl = questionsFilePath;
  //       const relativequestionDirectory = path.relative(projectRoot, questionDirectory);

  //       try {
  //         await downloadPDFs([pdfUrl], {
  //           outputDirectory: questionDirectory,
  //           filenameGenerator,
  //           timeoutMs: 30000,
  //           retries: 5,
  //           retryDelayMs: 2000,
  //           overwriteExisting: false,
  //         });
  //         downloadedSansadSessionQuestions.push({
  //           quesNo,
  //           subjects,
  //           lokNo,
  //           member,
  //           ministry,
  //           type,
  //           date,
  //           questionsFilePathWeb: questionsFilePath,
  //           questionsFilePathLocal: `${relativequestionDirectory}/${filenameGenerator(pdfUrl, 0)}`,
  //           questionsFilePathHindiWeb: questionsFilePathHindi,
  //         });
  //       } catch (error) {
  //         console.error('Error in downloading PDF: ', error);
  //         failedSansadSessionQuestionDownload.push(pdfUrl);
  //       }
  //     }
  //   }

  //   return {
  //     failedSansadSessionQuestionDownload,
  //     downloadedSansadSessionQuestions,
  //     status: failedSansadSessionQuestionDownload.length > 0 ? 'PARTIAL' : 'SUCCESS',
  //   };
}

fetchMetaAnalysisForQuestionsPdfs({ sansad: '18', session: 'iv' });
