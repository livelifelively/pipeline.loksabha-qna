import * as wf from '@temporalio/workflow';
import { tsActivity } from './activities';

const { proxyActivities } = wf;

const activities = proxyActivities({
  startToCloseTimeout: '60 second',
  taskQueue: 'ts-tasks-queue',
});

const pythonActivities = proxyActivities({
  startToCloseTimeout: '60 second',
  taskQueue: 'py-tasks-queue',
});

export async function multiLanguageWorkflow(initialString: string): Promise<string> {
  const tsResult = await activities.tsActivity(initialString);
  // IMPORTANT:  Data is passed as a JSON serializable object
  //  Here we are passing a string directly.
  //  For more complex objects, ensure proper serialization/deserialization.

  // The Workflow doesnt know (or care) which language the Activity will be executed in.
  // So we tell it to call pyActivity.
  const pyResult = await pythonActivities.pyActivity(tsResult);

  return pyResult;
}
