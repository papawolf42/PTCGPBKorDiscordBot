# Discord Message Format Analysis (`1.ahk`)

This document outlines the formats of messages sent from the `1.ahk` script to the Discord channel. This analysis is crucial for correctly parsing these messages in the `Poke.py` bot.

## 1. God Pack Found

This message is generated by the `GodPackFound` function in the AHK script.

### Message Format

```
{Interjection}
{username} ({friendCode})
[{starCount}/5][{packsInPool}P][{openPack}] {invalid} God Pack found in instance: {scriptName}
File name: {accountFile}
Backing up to the Accounts\GodPacks folder and continuing...
```

### Field Analysis

| Field | Example Value(s) | Description |
| :--- | :--- | :--- |
| `Interjection` | `Congrats!`, `GG!`, `Uh-oh!` | A random exclamation. |
| `username` | (string) | The player's username. Unpredictable. |
| `friendCode`| `0125709972794774` | 16-digit friend code. |
| `starCount` | `0`-`5` | Integer representing the number of stars. |
| `packsInPool`| (integer) | The number of packs. |
| `openPack` | `Palkia`, `Mewtwo`, etc. | The type of pack being opened. Possible values: `Mewtwo`, `Charizard`, `Pikachu`, `Mew`, `Dialga`, `Palkia`, `Arceus`, `Shining`, `Solgaleo`, `Lunala`, `Buzzwole`. |
| `invalid` | `Invalid` or (empty) | Indicates if the pack is invalid. Empty if valid. |
| `scriptName` | `1`, `2`, `3` | The script instance number. |
| `accountFile`| `20250606114618_3_Valid_2_packs.xml` | See detailed breakdown below. |

---

## 2. Special Card Found

This message is generated by the `FoundStars` function in the AHK script. This is the source of the "Trainer found by..." messages.

### Message Format

```
{star} found by {username} ({friendCode}) in instance: {scriptName} ({packsInPool} packs, {openPack})
File name: {accountFile}
Backing up to the Accounts\SpecificCards folder and continuing...
```

### Field Analysis

| Field | Example Value(s) | Description |
| :--- | :--- | :--- |
| `star` | `Trainer`, `FullArt`, `Shiny` | The type of special card found. Possible values derived from `Settings.ini`: `Trainer`, `FullArt`, `Rainbow`, `Shiny`, `Crown`, `Immersive`. |
| `username` | (string) | The player's username. |
| `friendCode`| `0125709972794774` | 16-digit friend code. |
| `scriptName` | `1`, `2`, `3` | The script instance number. |
| `packsInPool`| (integer) | The number of packs. |
| `openPack` | `Palkia`, `Mewtwo`, etc. | The type of pack being opened. Same list as God Pack. |
| `accountFile`| `20250606144606_3_Trainer_1_packs.xml` | See detailed breakdown below. |

---

## `accountFile` Field Breakdown

The `accountFile` field has a consistent structure.

### Format

`{timestamp}_{instance_id}_{status}_{pack_count}_packs.xml`

### Field Analysis

| Field | Example Value | Description |
| :--- | :--- | :--- |
| `timestamp` | `20250606144606` | Timestamp in `YYYYMMDDHHMMSS` format. |
| `instance_id`| `3` | The script instance number, same as `scriptName`. |
| `status` | `Valid`, `Trainer`, `Shiny` | The status or type of card found. |
| `pack_count`| `1` | The number of packs. |
 
 