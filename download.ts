import axios from "axios";
import fs from "fs";

async function download(url: string) {
  const response = await axios.get(url);
  return response.data;
}

async function downloadCreatures() {
  // Create a folder named "data" if it doesn't exist
  if (!fs.existsSync("data")) {
    fs.mkdirSync("data");
  }

  try {
    // Download the list of creature names
    const creatureNames: string[] = await download(
      "http://tibiawiki.dev/api/creatures"
    );

    // Set the concurrency limit
    const concurrencyLimit = 100;

    // Process creatures in parallel with a concurrency limit
    const promises = creatureNames.map(async (name: string) => {
      // Replace spaces with underscores in the name
      const formattedName = name.replace(/ /g, "_");

      // Download the creature data
      const creatureData = await download(
        `http://tibiawiki.dev/api/creatures/${formattedName}`
      );

      // Save the creature data as a JSON file
      const filename = `data/${formattedName}.json`;
      fs.writeFileSync(filename, JSON.stringify(creatureData, null, 4));

      console.log(`Saved ${filename}`);
    });

    // Execute the promises in parallel with the concurrency limit
    const results = await Promise.all(
      Array.from(
        { length: Math.ceil(promises.length / concurrencyLimit) },
        (_, index) =>
          Promise.all(
            promises.slice(
              index * concurrencyLimit,
              (index + 1) * concurrencyLimit
            )
          )
      )
    );

    console.log("Download complete!");
  } catch (error) {
    console.error("An error occurred:", error);
  }
}

downloadCreatures();
