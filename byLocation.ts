import fs from "fs";
import { execSync } from "child_process";

interface Creature {
  name: string;
  location: string;
}

// Read the creature JSON files
const files = fs.readdirSync("data");

// Create a map to store creatures by location
const creaturesByLocation = new Map<string, Creature[]>();

// Process each JSON file
files.forEach((file) => {
  const data = fs.readFileSync(`data/${file}`, "utf-8");
  const creature: Creature = JSON.parse(data);

  // Find the first location within double square brackets
  const match = creature.location?.match(/\[\[(.*?)\]\]/);
  const location = match ? match[1] : creature.location ?? "Unknown";

  // Add the creature to the respective location group
  if (!creaturesByLocation.has(location)) {
    creaturesByLocation.set(location, []);
  }
  creaturesByLocation.get(location)?.push(creature);
});

const issueList: { number: number; title: string }[] = JSON.parse(
  execSync(
    `gh issue list --repo luan/tibiawiki --limit 1000 -s open --json 'number,title'`
  ).toString()
);

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const isolated: any[] = [];
const groupsOf2: any[] = [];

async function createIssues() {
  for (const [location, creatures] of creaturesByLocation) {
    const issueTitle = `[auto] creatures in ${location}`.replace(/"/g, "'");
    if (creatures.length === 1) {
      const issue = issueList.find((issue) => issue.title === issueTitle);
      if (issue) {
        execSync(`gh issue close --repo luan/tibiawiki ${issue.number}`);
      }
      isolated.push(creatures[0]);
      continue;
    }
    if (creatures.length === 2) {
      const issue = issueList.find((issue) => issue.title === issueTitle);
      if (issue) {
        execSync(`gh issue close --repo luan/tibiawiki ${issue.number}`);
      }
      groupsOf2.push(creatures[0]);
      continue;
    }
    const issueBody = creatures
      .map((creature) => `- [ ] ${creature.name}`)
      .join("\n");

    if (issueList.find((issue) => issue.title === issueTitle)) {
      console.log(`Issue "${issueTitle}" already exists. Skipping creation.`);
    } else {
      // Create the issue using GitHub CLI
      execSync(
        `gh issue create  --repo luan/tibiawiki --title "${issueTitle}" --body "${issueBody}"`
      );
      console.log(`Created issue "${issueTitle}".`);
      await sleep(3000);
    }
  }
}

// create issues for the isolated creatures
async function createIsolatedIssues() {
  const issueTitle = `[auto] isolated creatures`;
  let issueBody = "";
  for (const creature of isolated) {
    issueBody += `- [ ] ${creature.name}\n`;
  }
  if (issueList.find((issue) => issue.title === issueTitle)) {
    console.log(`Issue "${issueTitle}" already exists. Skipping creation.`);
  } else {
    execSync(
      `gh issue create  --repo luan/tibiawiki --title "${issueTitle}" --body "${issueBody}"`
    );
    console.log(`Created issue "${issueTitle}".`);
  }
}

async function createGroupsOf2() {
  const issueTitle = `[auto] (groups of 2 -- merged) creatures`;
  let issueBody = "";
  for (const creature of groupsOf2) {
    issueBody += `- [ ] ${creature.name}\n`;
  }
  if (issueList.find((issue) => issue.title === issueTitle)) {
    console.log(`Issue "${issueTitle}" already exists. Skipping creation.`);
  } else {
    execSync(
      `gh issue create  --repo luan/tibiawiki --title "${issueTitle}" --body "${issueBody}"`
    );
    console.log(`Created issue "${issueTitle}".`);
  }
}

async function createAll() {
  await createIssues();
  await createIsolatedIssues();
  await createGroupsOf2();
}

createAll();
