// startWorkflow.ts
import { Client, Connection } from '@temporalio/client';

async function run() {
  const connection = await Connection.connect({
    address: 'localhost:7233'
  });

  const client = new Client({
    connection,
    namespace: 'default',
  });

  const workflowId = 'multi-language-workflow-' + Date.now();
  const handle = await client.workflow.start('multiLanguageWorkflow', {
    taskQueue: 'ts-tasks-queue',
    workflowId: workflowId,
    args: ["Initial String"],
  });

  console.log(`Started workflow ${workflowId}`);
  console.log(`Workflow result: ${await handle.result()}`);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});