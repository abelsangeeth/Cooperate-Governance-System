CREATE TABLE Stakeholder (
    StakeholderID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Role ENUM('Shareholder', 'Board Member', 'Executive') NOT NULL,
    ContactInfo VARCHAR(100),
    SharesOwned INT
);
CREATE TABLE BoardMeeting (
    MeetingID INT PRIMARY KEY AUTO_INCREMENT,
    Date DATE NOT NULL,
    Time TIME NOT NULL,
    Agenda TEXT,
    Location VARCHAR(100)
);


CREATE TABLE ComplianceDocument (
    DocumentID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(255) NOT NULL,
    Type ENUM('Policy', 'License', 'Certification', 'Report') NOT NULL,
    ExpiryDate DATE,
    Status ENUM('Active', 'Expired', 'Pending Renewal') NOT NULL
);

CREATE TABLE Decision (
    DecisionID INT PRIMARY KEY AUTO_INCREMENT,
    MeetingID INT,
    Description TEXT NOT NULL,
    Rationale TEXT,
    Status ENUM('Pending', 'Implemented') NOT NULL,
    FOREIGN KEY (MeetingID) REFERENCES BoardMeeting(MeetingID) ON DELETE CASCADE
);

CREATE TABLE Audit (
    AuditID INT PRIMARY KEY AUTO_INCREMENT,
    Date DATE NOT NULL,
    Findings TEXT,
    Recommendations TEXT,
    Status ENUM('Open', 'Closed') NOT NULL
);

CREATE TABLE Policy (
    PolicyID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(255) NOT NULL,
    Version VARCHAR(50),
    ApprovalDate DATE,
    Category ENUM('Code of Conduct', 'Ethics', 'Financial') NOT NULL
);

CREATE TABLE PerformanceEvaluation (
    EvaluationID INT PRIMARY KEY AUTO_INCREMENT,
    StakeholderID INT,
    Metrics TEXT,
    Feedback TEXT,
    Score INT,
    FOREIGN KEY (StakeholderID) REFERENCES Stakeholder(StakeholderID) ON DELETE CASCADE
);

CREATE TABLE ConflictOfInterest (
    ConflictID INT PRIMARY KEY AUTO_INCREMENT,
    StakeholderID INT,
    Description TEXT,
    Status ENUM('Disclosed', 'Resolved') NOT NULL,
    FOREIGN KEY (StakeholderID) REFERENCES Stakeholder(StakeholderID) ON DELETE CASCADE
);
CREATE TABLE User (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    LastLogin DATETIME,
    Role ENUM('Admin', 'Board Member', 'Auditor') NOT NULL
);