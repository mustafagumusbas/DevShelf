import sqlite3
import os

skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Discord'])]
statuses = [ (_,) for _ in (['Prototip Oluşturma', 'Geliştirme Aşamasında', 'Tamamlandı, kullanıma hazır', 'Güncellendi', 'Tamamlandı, ancak bakımı yapılmadı'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database
        if not os.path.exists(self.database):
            self.create_tables()
            self.default_insert()
        self.add_screenshot_column()


    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def add_screenshot_column(self):
        conn = sqlite3.connect(self.database)
        try:
            with conn:
                conn.execute("ALTER TABLE projects ADD COLUMN screenshot TEXT")
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()

    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()

    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)

    def insert_project(self, data):
        """
        Accepts a list of tuples (for executemany style).
        Expected item formats (according to your examples):
          - 4-tuple: (user_id, project_name, url, status_id)
          - 5-tuple: (user_id, project_name, url, status_id, description)
        """
        if not data or not isinstance(data, (list, tuple)):
            return "hatalı giriş"

        first = data[0]
        if len(first) == 4:
            sql = "INSERT INTO projects (user_id, project_name, url, status_id) VALUES(?, ?, ?, ?)"
        elif len(first) == 5:
            sql = "INSERT INTO projects (user_id, project_name, url, status_id, description) VALUES(?, ?, ?, ?, ?)"
        else:
            return "hatalı giriş"
        self.__executemany(sql, data)
    
    def insert_skill(self, user_id, project_name, skill):
        # find project
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        res = self.__select_data(sql, (project_name, user_id))
        if not res:
            return None
        project_id = res[0][0]

        # ensure skill exists
        res2 = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))
        if not res2:
            # insert skill then fetch id
            self.__executemany('INSERT INTO skills (skill_name) VALUES (?)', [(skill,)])
            res2 = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))
            if not res2:
                return None
        skill_id = res2[0][0]

        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills (project_id, skill_id) VALUES(?, ?)'
        self.__executemany(sql, data)
        return True

    def get_statuses(self):
        sql="SELECT status_name from status"
        return self.__select_data(sql)

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_projects(self, user_id):
        sql = "SELECT * FROM projects WHERE user_id = ?"
        return self.__select_data(sql, data = (user_id,))

    def get_project_id(self, project_name, user_id):
        res = self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))
        if not res:
            return None
        return res[0][0]

    def get_skills(self):
        return self.__select_data(sql='SELECT * FROM skills')

    def get_project_skills(self, project_name):
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
JOIN project_skills ON projects.project_id = project_skills.project_id 
JOIN skills ON skills.skill_id = project_skills.skill_id 
WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])

    def get_project_info(self, user_id, project_name):
        sql = """
SELECT project_name, description, url, status_name FROM projects 
JOIN status ON
status.status_id = projects.status_id
WHERE project_name=? AND user_id=?
"""
        return self.__select_data(sql=sql, data = (project_name, user_id))

    def update_projects(self, param, data):
        sql = f"UPDATE projects SET {param} = ? WHERE project_name = ? AND user_id = ?"
        self.__executemany(sql, [data])

    def delete_project(self, user_id, project_id):
        sql = "DELETE FROM project_skills WHERE project_id = ?"
        self.__executemany(sql, [(project_id,)])
        sql = """DELETE FROM projects 
WHERE user_id = ? AND project_id = ? """
        self.__executemany(sql, [(user_id, project_id)])

    def delete_skill(self, project_id, skill_id):
        sql = "DELETE FROM project_skills WHERE skill_id = ? AND project_id = ?"
        self.__executemany(sql, [(skill_id, project_id)])


if __name__ == '__main__':
    manager = DB_Manager("prob.db")