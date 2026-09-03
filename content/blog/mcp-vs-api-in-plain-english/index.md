---
title: "MCP vs API, in Plain English"
date: 2026-09-03
category: POV
excerpt: MCP vs API, explained without the tech jargon — why the difference decides whether your AI is a shortcut or a second brain for your client relationships.
cover: cover.png
draft: false
tags: [mcp, api, artificial-intelligence, client-intelligence, ai-for-cavemen]
---

If you got here from the reel, good news: the caveman was basically right.

Here is the same thing in full sentences, with no technical background needed.

## The question everyone is actually asking

You are being asked whether your AI "integrates" with your systems. Somewhere in the answer, someone says API. Someone else says MCP. Both sound like the same kind of thing. They are related, but they are not the same, and the difference is worth two minutes of your time, because it decides whether your AI is a shortcut or a second brain.

## An API is a vending machine

An API is how two bits of software pass information to each other. It has been the standard way to do this for two decades, and it works.

Think of it as a vending machine. Someone decided what goes in it and which button gets you what. Press B4, get the thing in B4. Every time, no surprises.

That reliability is the point. It is also the limit. You can only get what somebody stocked. If you want something that is not in the machine, you raise a request, wait for someone technical to build it, and hope it arrives before the quarter ends.

There is a second problem nobody mentions in the sales meeting. The machine does not come with a label anyone else can read. Every AI tool that wants to use it needs a developer to study the manual and write code for that one machine. Four AI tools that each need to reach five of your systems is twenty separate builds, each one needing maintenance. This is why so much agency reporting still ends up in a spreadsheet somebody updates manually on a Monday.

## MCP is a vending machine that describes itself

MCP stands for Model Context Protocol. It is a shared standard for how AI connects to the systems where your work lives. Anthropic published it in late 2024 and then gave it away in December 2025, to an open foundation whose backers now include Anthropic, OpenAI, Google, Microsoft, Amazon and Block. Nobody owns it, which matters when you are being asked to standardise on something.

Here is where most explanations, including our own reel, go a little too far. They tell you that with an API a developer decides in advance what you can ask, and with MCP the AI decides. That is not quite it.

An MCP server also offers a fixed set of things it can do, and a developer still decided what those are. The vending machine does not disappear. Three things change about it.

**The machine describes itself.** Everything it can do comes with a plain-language label the AI reads at the moment you ask your question. So any AI tool that speaks MCP can walk up to any system that speaks MCP and work out what is on offer, without anyone writing code for that specific pair. Twenty builds becomes nine.

**The AI presses several buttons in a row.** This is the part that actually feels like magic. One button gets you a client's meeting history. Another gets you what they committed to. Another gets you how the relationship has been trending. No single button answers "why is this account wobbling", but a sequence of them does, and nobody had to anticipate that sequence and build a report for it.

**What comes back is written for a reader.** An API answers in a format built for another piece of software to process. MCP answers in a form the AI can reason about, which is why it can act on the answer rather than just display it.

So you do not stop being limited by what your systems can do. You stop being limited to the combinations somebody thought of twelve months ago. That is a smaller-sounding difference than it is.

The comparison people use is a USB-C cable. One standard connector, so anything plugs into anything, instead of a drawer full of chargers that each only fit one device.

## Where the caveman oversimplified

In the reel, the friend already knows the answer. Not quite.

Your AI still has to go and look things up, using tools somebody built. What changes is that it works out which of those tools to use, and in what order, in the moment, rather than following a script written by someone who was guessing at your job.

## What it looks like on a Tuesday morning

Ninety minutes before a renewal conversation.

With a traditional integration, you have a dashboard. It answers the questions it was built to answer. It will not tell you about the three things you promised on a call in March that quietly never got done.

With MCP, you just ask. In your own words.

One of our clients put it like this:

> "I probably on a daily basis interrogate Kaizan — take me back to this meeting where so-and-so was talking about such-and-such. Without Kaizan, what's the alternative? Just reaching into the deepest recesses of your mind, which is obviously flawed."

That is the real unlock. Not another report. The ability to go digging through a whole client history without knowing in advance what you are looking for.

## Four things to keep in mind

**MCP does not replace APIs.** It mostly sits on top of them. The API still moves the data. MCP is what makes that data make sense to an AI, and what saves you a bespoke build for every tool you want to connect.

**It does not replace your security questions.** If anything, ask more of them. When the AI is choosing what to access rather than following a fixed script, you want to know exactly what it can and cannot reach.

**Ask specifically about prompt injection.** This is the one risk that is genuinely new. Because the AI reads text to decide what to do next, text it reads can try to instruct it. A malicious line buried in a document or an email can attempt to talk your AI into fetching something it should not, or sending it somewhere it should not go. A hardcoded integration cannot be talked into anything. Ask any vendor how they handle this before you connect anything.

**It is only as good as what is underneath.** Connect an AI to a folder of raw meeting transcripts and you get a fast way to search transcripts. Connect it to a system that has already tracked every commitment, scored every relationship and flagged every risk, and you get something far more useful.

## What this looks like with Kaizan

Kaizan runs an MCP server, which means you can point Claude or any other AI tool that speaks the standard straight at your client portfolio. No export, no dashboard, no waiting on a build at your end.

What it can reach:

- Your client list, including tiers, so you can ask about one account or a whole segment
- CARE scores, both the latest picture and how each score has moved over the last year
- A ranking of your whole portfolio, worst accounts first, because that is the list that needs acting on
- Every meeting, including summaries you can search by meaning rather than keyword, and full transcripts when you need the exact words
- Sentiment moments, from a client quietly going cold to a genuine high point worth building on
- Action items, and whether they actually got done

That is a fixed list, and we decided what is on it. The point is what happens when an AI can combine them. The questions stop being "what does the report show" and start being:

Which of my accounts are at risk right now. Has responsiveness on this client improved since we changed the team. What did they say about the budget in the spring. What did we promise on the last three calls, and did any of it happen.

None of those has a button. All of them are answerable.

Two things are worth being clear about, because they are our engineering rather than gifts from the protocol. Searching meetings by meaning rather than keyword is something we built. So is the permission model: ask about your own meetings and actions and you get yours, ask about the portfolio and you only ever see the clients you have access to. The AI can reach a lot, but not more than you can. MCP hands you neither of those for free, so it is a fair question to put to any vendor.

## The short version

APIs are how software passes data around. MCP is a standard way to hand an AI a labelled set of things it can do with that data, and let it work out which ones your question needs.

The truth on every client relationship, and the AI Helpers to act on it.

The caveman was close enough. MCP is the one that makes AI actually useful.
