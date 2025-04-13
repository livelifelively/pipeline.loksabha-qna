import fs from "fs";
import path from "path";
import axios from "axios";
import { promisify } from "util";
import stream from "stream";

const finished = promisify(stream.finished);

interface DownloadOptions {
  outputDirectory?: string;
  filenameGenerator?: (url: string, index: number) => string;
  timeoutMs?: number; // Added timeout option
  retries?: number; // Added retry option
  retryDelayMs?: number; // Added retry delay option
  overwriteExisting?: boolean; // Add overwrite option
}

export async function downloadPDFs(urls: string[], options: DownloadOptions = {}): Promise<void> {
  const {
    outputDirectory = "./downloads", // Default output directory
    filenameGenerator = (url, index) => `file_${index}.pdf`, // Default filename generator
    timeoutMs = 60000, // Default timeout: 60 seconds
    retries = 3, // Default number of retries
    retryDelayMs = 1000, // Default retry delay: 1 second
    overwriteExisting = false, // Default: do not overwrite
  } = options;

  // Create the output directory if it doesn't exist
  if (!fs.existsSync(outputDirectory)) {
    fs.mkdirSync(outputDirectory, { recursive: true }); // Use recursive: true for nested directories
  }

  for (const [index, url] of urls.entries()) {
    const filename = filenameGenerator(url, index);
    const filePath = path.join(outputDirectory, filename);

    if (fs.existsSync(filePath) && !overwriteExisting) {
      console.warn(`File ${filePath} already exists. Skipping download.`);
      continue; // Skip this download
    }

    let successfulDownload = false;
    let attempts = 0;

    while (!successfulDownload && attempts < retries) {
      attempts++;
      try {
        console.log(`Downloading ${url} to ${filePath} (attempt ${attempts} of ${retries})`);

        const response = await axios.get(url, {
          responseType: "stream",
          timeout: timeoutMs,
        });

        const writer = fs.createWriteStream(filePath);

        response.data.pipe(writer);

        await finished(writer);
        successfulDownload = true;
        console.log(`Successfully downloaded ${url} to ${filePath}`);
      } catch (error: any) {
        // Explicitly type error as any (or unknown in stricter TS)
        if (attempts < retries) {
          console.error(`Failed to download ${url} (attempt ${attempts}). Retrying in ${retryDelayMs}ms...`);
          if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            console.error("  Error Response Status:", error.response.status);
            console.error("  Error Response Headers:", error.response.headers);
          } else if (error.request) {
            // The request was made but no response was received
            // `error.request` is an instance of XMLHttpRequest in the browser and an instance of
            // http.ClientRequest in node.js
            console.error("  Error: No response received. Request:", error.request);
          } else if (error.code === "ECONNABORTED") {
            console.error("  Error: Request timed out.");
          } else {
            // Something happened in setting up the request that triggered an Error
            console.error("  Error Message:", error.message);
          }
          console.error("   Error Stack:", error.stack);
          await new Promise((resolve) => setTimeout(resolve, retryDelayMs)); // Wait before retrying
        } else {
          console.error(`Failed to download ${url} after ${retries} attempts.  Error: ${error.message}`);
        }
      }
    }
  }
}
