const express = require("express");
const bodyParser = require("body-parser");
const mysql = require("mysql");

const connection = mysql.createPool({
  host: "s11.liara.ir",
  user: "root",
  password: "T2uKgpP6yipXBYAoX1pW4KJo",
  database: "tvinfo",
  port: 33295,
});

const app = express();

// Creating a GET route that returns data from the 'users' table.
app.get("/recommend", function (req, res) {
  // Connecting to the database.
  connection.getConnection(function (err, connection) {
    // Executing the MySQL query (select all data from the 'users' table).
    connection.query("SELECT * FROM recommend", function (
      error,
      results,
      fields
    ) {
      // If some error occurs, we throw an error.
      if (error) throw error;

      // Getting the 'response' from the database and sending it to our route. This is were the data is.
      res.send(results);
    });
  });
});

app.listen(8000, () => {
  console.log("you can see the data.");
});
