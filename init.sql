-- Таблица hacker
CREATE TABLE hacker (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_hacker_user_id UNIQUE (user_id)
);

-- Таблица ролей
CREATE TABLE role (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT uq_role_name UNIQUE (name)
);

-- Таблица для связи hacker и role (many-to-many)
CREATE TABLE hacker_role_association (
    hacker_id UUID NOT NULL,
    role_id UUID NOT NULL,
    PRIMARY KEY (hacker_id, role_id),
    FOREIGN KEY (hacker_id) REFERENCES hacker (id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES role (id) ON DELETE CASCADE
);

-- Таблица team
CREATE TABLE team (
    id UUID PRIMARY KEY,
    owner_id UUID NOT NULL,
    name TEXT NOT NULL,
    max_size INTEGER NOT NULL CHECK (max_size > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES hacker (id) ON DELETE CASCADE,

    CONSTRAINT uq_team_owner_id_name UNIQUE (owner_id, name)
);

-- Таблица для связи hacker и team (many-to-many)
CREATE TABLE hacker_team_association (
    hacker_id UUID NOT NULL,
    team_id UUID NOT NULL,
    PRIMARY KEY (hacker_id, team_id),
    FOREIGN KEY (hacker_id) REFERENCES hacker (id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES team (id) ON DELETE CASCADE
);

-- Таблица hackathon
CREATE TABLE hackathon (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    task_description TEXT,
    start_of_registration TIMESTAMP WITH TIME ZONE,
    end_of_registration TIMESTAMP WITH TIME ZONE,
    start_of_hack TIMESTAMP WITH TIME ZONE NOT NULL,
    end_of_hack TIMESTAMP WITH TIME ZONE,
    amount_money FLOAT,
    type TEXT, -- "online" или "offline"
    url TEXT, -- URL страницы хакатона
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_name_start_of_hack UNIQUE (name, start_of_hack)
);

-- Таблица winner_solution
CREATE TABLE winner_solution (
    id UUID PRIMARY KEY,
    win_money FLOAT NOT NULL,
    link_to_solution TEXT NOT NULL,
    link_to_presentation TEXT NOT NULL,
    can_share BOOLEAN DEFAULT TRUE NOT NULL,
    hackathon_id UUID NOT NULL,
    team_id UUID NOT NULL,
    FOREIGN KEY (hackathon_id) REFERENCES hackathon (id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES team (id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_winner_solution_hackathon_id_team_id UNIQUE (hackathon_id, team_id)
);
