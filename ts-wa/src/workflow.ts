import * as wf from '@temporalio/workflow';
import { tsActivity } from './activities';

const { proxyActivities } = wf;

// const activities = proxyActivities({
//   // #FIXED: The workflow was reinitiating without completion.
//   // causing issues when I was debugging. after certain time it would just restart and take control back to initial point.
//   // the issue was small timeout (60 seconds)
//   // so I increased it to 600 seconds.
//   startToCloseTimeout: '60000 second',
//   taskQueue: 'ts-tasks-queue',
// });

const pythonActivities = proxyActivities({
  startToCloseTimeout: '60 second',
  taskQueue: 'py-tasks-queue',
});

export async function multiLanguageWorkflow(initialString: string): Promise<string> {
  // const tsResult = await activities.tsActivity(initialString);
  // IMPORTANT:  Data is passed as a JSON serializable object
  //  Here we are passing a string directly.
  //  For more complex objects, ensure proper serialization/deserialization.

  // The Workflow doesnt know (or care) which language the Activity will be executed in.
  // So we tell it to call pyActivity.
  // console.log('Calling Python activity with input:', tsResult);
  const pyResult = await pythonActivities.process_questions('Hello World');

  // return pyResult;
  return 'Hello World';
}
