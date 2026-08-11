// 1. Define Admin Dashboard Component
const AdminDashboard = {
    template: `
        <div class="container mt-4 mb-5">
           <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Admin Dashboard</h2>
                <div>
                    <button @click="triggerEmail" class="btn btn-primary btn-sm me-2">Test Daily Email</button>
                    <button @click="logout" class="btn btn-danger btn-sm">Logout</button>
                </div>
            </div>
            
            <div v-if="error" class="alert alert-danger shadow-sm">{{ error }}</div>

            <!-- Statistics Cards -->
            <div class="row mb-4 text-center">
                <div class="col-md-3"><div class="card bg-primary text-white p-3 shadow"><h5>Students</h5><h3>{{ stats.total_students }}</h3></div></div>
                <div class="col-md-3"><div class="card bg-success text-white p-3 shadow"><h5>Companies</h5><h3>{{ stats.total_companies }}</h3></div></div>
                <div class="col-md-3"><div class="card bg-info text-white p-3 shadow"><h5>Drives</h5><h3>{{ stats.total_drives }}</h3></div></div>
                <div class="col-md-3"><div class="card bg-warning text-dark p-3 shadow"><h5>Applications</h5><h3>{{ stats.total_applications }}</h3></div></div>
            </div>

            <!-- Registered Companies Section -->
            <div class="card shadow mb-4">
                <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
                    <span class="mb-0">Registered Companies</span>
                    <input type="text" v-model="companySearch" @input="fetchCompanies" class="form-control form-control-sm w-25" placeholder="Search companies...">
                </div>
                <div class="card-body">
                    <table class="table table-striped">
                        <thead>
                            <tr><th>Name</th><th>HR Contact</th><th>Status</th><th>Account</th><th>Action</th></tr>
                        </thead>
                        <tbody>
                            <tr v-for="c in companies" :key="c.id">
                                <td class="fw-bold">{{ c.name }}</td>
                                <td>{{ c.hr_contact }}</td>
                                <td>
                                    <span v-if="c.is_approved" class="badge bg-success">Approved</span>
                                    <span v-else class="badge bg-warning text-dark">Pending</span>
                                </td>
                                <td>
                                    <span v-if="c.is_active" class="badge bg-primary">Active</span>
                                    <span v-else class="badge bg-danger">Blacklisted</span>
                                </td>
                                <td>
                                    <button v-if="!c.is_approved" @click="approveCompany(c.id)" class="btn btn-sm btn-success me-1">Approve</button>
                                    <button @click="toggleUserStatus(c.user_id)" :class="['btn btn-sm', c.is_active ? 'btn-danger' : 'btn-outline-secondary']">
                                        {{ c.is_active ? 'Blacklist' : 'Restore' }}
                                    </button>
                                </td>
                            </tr>
                            <tr v-if="companies.length === 0"><td colspan="5" class="text-center">No companies found.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Registered Students Section -->
            <div class="card shadow mb-4">
                <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
                    <span class="mb-0">Registered Students</span>
                    <input type="text" v-model="studentSearch" @input="fetchStudents" class="form-control form-control-sm w-25" placeholder="Search by name/roll no...">
                </div>
                <div class="card-body">
                    <table class="table table-striped">
                        <thead>
                            <tr><th>Name</th><th>Roll Number</th><th>Branch</th><th>CGPA</th><th>Account</th><th>Action</th></tr>
                        </thead>
                        <tbody>
                            <tr v-for="s in students" :key="s.id">
                                <td class="fw-bold">{{ s.name }}</td>
                                <td>{{ s.roll_number }}</td>
                                <td>{{ s.branch }}</td>
                                <td>{{ s.cgpa }}</td>
                                <td>
                                    <span v-if="s.is_active" class="badge bg-primary">Active</span>
                                    <span v-else class="badge bg-danger">Blacklisted</span>
                                </td>
                                <td>
                                    <button @click="toggleUserStatus(s.user_id)" :class="['btn btn-sm', s.is_active ? 'btn-danger' : 'btn-outline-secondary']">
                                        {{ s.is_active ? 'Blacklist' : 'Restore' }}
                                    </button>
                                </td>
                            </tr>
                            <tr v-if="students.length === 0"><td colspan="6" class="text-center">No students found.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Admin Applications View -->
            <div class="card shadow mb-5">
                <div class="card-header bg-warning text-dark font-weight-bold">
                    Platform Job Applications
                </div>
                <div class="card-body p-0">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Student Name</th>
                                <th>Company</th>
                                <th>Job Role</th>
                                <th>Current Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="app in applications" :key="app.id">
                                <td><strong>{{ app.student_name }}</strong></td>
                                <td>{{ app.company_name }}</td>
                                <td>{{ app.job_title }}</td>
                                <td><span class="badge bg-secondary">{{ app.status }}</span></td>
                            </tr>
                            <tr v-if="applications.length === 0">
                                <td colspan="4" class="text-center p-3 text-muted">No applications on the platform yet.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            stats: { total_students: 0, total_companies: 0, total_drives: 0, total_applications: 0 },
            companies: [],
            students: [],
            applications: [],
            companySearch: '',
            studentSearch: '',
            error: null
        }
    },
    async mounted() {
        if (!localStorage.getItem('token') || localStorage.getItem('role') !== 'admin') {
            this.$router.push('/');
            return;
        }
        await this.fetchStats();
        await this.fetchCompanies();
        await this.fetchStudents(); 
        await this.fetchApplications(); 
    },
    methods: {
        getHeaders() {
            return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token') };
        },
        async fetchStats() {
            try {
                const res = await fetch('/api/admin/stats', { headers: this.getHeaders() });
                if (res.ok) this.stats = await res.json();
                else this.error = "Failed to load stats.";
            } catch (err) { this.error = "Server connection error."; }
        },
        async fetchCompanies() {
            try {
                const res = await fetch('/api/admin/companies?search=' + this.companySearch, { headers: this.getHeaders() });
                if (res.ok) this.companies = await res.json();
            } catch (err) { console.error("Error fetching companies"); }
        },
        async fetchStudents() {
            try {
                const res = await fetch('/api/admin/students?search=' + this.studentSearch, { headers: this.getHeaders() });
                if (res.ok) this.students = await res.json();
            } catch (err) { console.error("Error fetching students"); }
        },
        async fetchApplications() {
            try {
                const res = await fetch('/api/admin/applications', { headers: this.getHeaders() });
                if (res.ok) this.applications = await res.json();
            } catch (err) { console.error("Error fetching applications"); }
        },
        async approveCompany(companyId) {
            try {
                const res = await fetch('/api/admin/company/' + companyId + '/approve', {
                    method: 'POST',
                    headers: this.getHeaders()
                });
                if (res.ok) await this.fetchCompanies();
            } catch (err) { console.error("Error approving company"); }
        },
        async toggleUserStatus(userId) {
            try {
                const res = await fetch('/api/admin/user/' + userId + '/toggle_active', {
                    method: 'POST',
                    headers: this.getHeaders()
                });
                if (res.ok) {
                    await this.fetchCompanies();
                    await this.fetchStudents();
                } else {
                    const data = await res.json();
                    alert(data.message);
                }
            } catch (err) { console.error("Error toggling user status"); }
        },
        async triggerEmail() {
            try {
                const res = await fetch('/api/admin/test-email', { headers: this.getHeaders() });
                if (res.ok) {
                    alert("✅ Background Task Triggered! Check the terminal and your inbox.");
                } else {
                    alert("Failed to trigger email task.");
                }
            } catch (err) { 
                console.error("Error triggering email"); 
            }
        },
        logout() {
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            this.$router.push('/');
        }
    }
};
// 2. Define Company Dashboard Component
const CompanyDashboard = {
    template: `
        <div class="container mt-4 mb-5">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Company Dashboard <span v-if="stats.company_name" class="text-primary">- {{ stats.company_name }}</span></h2>
                <div>
                    <!-- THE MISSING EXPORT BUTTON -->
                    <button @click="exportCSV" class="btn btn-success btn-sm me-2">
                        <span v-if="isExporting">Exporting...</span>
                        <span v-else>Export Applications (CSV)</span>
                    </button>
                    <button @click="logout" class="btn btn-danger btn-sm">Logout</button>
                </div>
            </div>

            <div v-if="success" class="alert alert-success shadow-sm" v-html="success"></div>
            
            <div v-if="error" class="alert alert-warning text-center p-5 shadow">
                <h4>Access Restricted</h4><p class="mb-0">{{ error }}</p>
            </div>

            <div v-if="!error">
                <div class="row mb-4">
                    <div class="col-md-6"><div class="card bg-info text-white text-center p-3 shadow"><h4>Total Drives</h4><h2>{{ stats.total_drives }}</h2></div></div>
                    <div class="col-md-6"><div class="card bg-success text-white text-center p-3 shadow"><h4>Applications Received</h4><h2>{{ stats.total_applications }}</h2></div></div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card shadow h-100">
                            <div class="card-header bg-dark text-white">Post a New Job Drive</div>
                            <div class="card-body">
                                <form @submit.prevent="createDrive">
                                    <div class="mb-2"><label class="form-label">Job Title</label><input type="text" v-model="form.job_title" class="form-control form-control-sm" required></div>
                                    <div class="mb-2"><label class="form-label">Description</label><textarea v-model="form.job_description" class="form-control form-control-sm" rows="2" required></textarea></div>
                                    <div class="mb-2"><label class="form-label">Eligible Branches</label><input type="text" v-model="form.eligibility_branch" class="form-control form-control-sm"></div>
                                    <div class="mb-2"><label class="form-label">Min CGPA</label><input type="number" step="0.01" v-model="form.eligibility_cgpa" class="form-control form-control-sm"></div>
                                    <div class="mb-3"><label class="form-label">Deadline</label><input type="date" v-model="form.deadline" class="form-control form-control-sm" required></div>
                                    <button type="submit" class="btn btn-primary btn-sm w-100">Post Drive</button>
                                </form>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-8">
                        <div class="card shadow h-100">
                            <div class="card-header bg-secondary text-white">Your Placement Drives</div>
                            <div class="card-body" style="overflow-y: auto; max-height: 400px;">
                                <table class="table table-sm table-striped">
                                    <thead><tr><th>Job Title</th><th>Deadline</th><th>Status</th><th>Action</th></tr></thead>
                                    <tbody>
                                        <tr v-for="drive in drives" :key="drive.id">
                                            <td>{{ drive.job_title }}</td><td>{{ drive.deadline }}</td>
                                            <td><span :class="drive.status === 'Active' ? 'badge bg-success' : 'badge bg-danger'">{{ drive.status }}</span></td>
                                            <td>
                                                <button @click="toggleDrive(drive.id)" class="btn btn-sm btn-outline-dark">
                                                    {{ drive.status === 'Active' ? 'Close Job' : 'Reopen' }}
                                                </button>
                                            </td>
                                        </tr>
                                        <tr v-if="drives.length === 0"><td colspan="4" class="text-center">No drives posted yet.</td></tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="card shadow mb-5">
                    <div class="card-header bg-primary text-white">Student Applications (Review, Resume & Schedule)</div>
                    <div class="card-body">
                        <table class="table table-hover align-middle">
                            <thead>
                                <tr><th>Student Details & Skills</th><th>Job</th><th>Status</th><th>Provide Feedback & Interview Date</th><th>Action</th></tr>
                            </thead>
                            <tbody>
                                <tr v-for="app in applications" :key="app.id">
                                    <td>
                                        <strong>{{ app.student_name }}</strong><br>
                                        <small class="text-muted">Branch: {{ app.student_branch }} | CGPA: {{ app.student_cgpa }}</small><br>
                                        <span class="d-block small text-dark mt-1"><strong>Skills:</strong> {{ app.student_skills || 'None listed' }}</span>
                                        <a v-if="app.student_resume" :href="app.student_resume" target="_blank" class="btn btn-sm btn-outline-secondary mt-1">📄 View Resume</a>
                                        <span v-else class="text-muted small d-block mt-1">No resume uploaded</span>
                                    </td>
                                    <td>{{ app.job_title }}</td>
                                    <td><span class="badge bg-secondary">{{ app.status }}</span></td>
                                    <td style="min-width: 200px;">
                                        <div v-if="app.status === 'Applied' || app.status === 'Shortlisted'">
                                            <input type="date" v-model="app.new_date" class="form-control form-control-sm mb-1" placeholder="Interview Date">
                                            <input type="text" v-model="app.new_feedback" class="form-control form-control-sm" placeholder="Feedback/Notes...">
                                        </div>
                                        <div v-else>
                                            <small><strong>Date:</strong> {{ app.interview_date || 'N/A' }}</small><br>
                                            <small><strong>Notes:</strong> {{ app.feedback || 'None' }}</small>
                                        </div>
                                    </td>
                                    <td>
                                        <div v-if="app.status === 'Applied' || app.status === 'Shortlisted'" class="btn-group btn-group-sm">
                                            <button @click="updateApp(app, 'Shortlisted')" class="btn btn-outline-primary">Shortlist</button>
                                            <button @click="updateApp(app, 'Selected')" class="btn btn-outline-success">Select</button>
                                            <button @click="updateApp(app, 'Rejected')" class="btn btn-outline-danger">Reject</button>
                                        </div>
                                        <span v-else class="text-muted small">Processed</span>
                                    </td>
                                </tr>
                                <tr v-if="applications.length === 0"><td colspan="5" class="text-center">No applications received yet.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            stats: { company_name: '', total_drives: 0, total_applications: 0 },
            drives: [], applications: [], 
            form: { job_title: '', job_description: '', eligibility_branch: '', eligibility_cgpa: '', deadline: '' },
            error: null,
            success: null,
            isExporting: false
        }
    },
    async mounted() {
        if (!localStorage.getItem('token') || localStorage.getItem('role') !== 'company') return this.$router.push('/');
        await this.fetchStats();
        if (!this.error) { await this.fetchDrives(); await this.fetchApplications(); }
    },
    methods: {
        getHeaders() { return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token') }; },
        async fetchStats() {
            try {
                const res = await fetch('/api/company/stats', { headers: this.getHeaders() });
                if (res.ok) this.stats = await res.json();
                else { const err = await res.json(); this.error = err.message; }
            } catch (err) { this.error = "Server error."; }
        },
        async fetchDrives() {
            const res = await fetch('/api/company/drives', { headers: this.getHeaders() });
            if (res.ok) this.drives = await res.json();
        },
        async fetchApplications() {
            const res = await fetch('/api/company/applications', { headers: this.getHeaders() });
            if (res.ok) {
                const apps = await res.json();
                this.applications = apps.map(a => ({ ...a, new_feedback: a.feedback || '', new_date: a.interview_date || '' }));
            }
        },
        
        async toggleDrive(driveId) {
            await fetch('/api/company/drives/' + driveId + '/toggle', { method: 'POST', headers: this.getHeaders() });
            await this.fetchDrives();
        },
        async updateApp(app, status) {
            await fetch('/api/company/application/' + app.id + '/status', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ status: status, feedback: app.new_feedback, interview_date: app.new_date })
            });
            await this.fetchApplications(); 
        },
        async createDrive() {
            const res = await fetch('/api/company/drives', { method: 'POST', headers: this.getHeaders(), body: JSON.stringify(this.form) });
            if (res.ok) {
                this.form = { job_title: '', job_description: '', eligibility_branch: '', eligibility_cgpa: '', deadline: '' };
                await this.fetchStats(); await this.fetchDrives();
            } else alert("Failed to create drive.");
        },
        async exportCSV() {
            this.error = null; this.success = null; this.isExporting = true;
            try {
                const res = await fetch('/api/company/export', { method: 'POST', headers: this.getHeaders() });
                const data = await res.json();
                if (res.ok) {
                    this.success = `${data.message} <br> <a href="${data.download_url}" target="_blank" class="btn btn-sm btn-link mt-2">Download File Here</a>`;
                } else {
                    this.error = data.message || "Failed to trigger export.";
                }
            } catch (err) {
                this.error = "Server error while exporting.";
            } finally {
                this.isExporting = false;
            }
        },
        logout() { localStorage.clear(); this.$router.push('/'); }
    }
};
// 3. Define Student Dashboard Component
// 3. Define Student Dashboard Component
const StudentDashboard = {
    template: `
        <div class="container mt-4 mb-5">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Student Dashboard <span v-if="studentName" class="text-primary">- Welcome, {{ studentName }}</span></h2>
                <div>
                    <button @click="exportCSV" class="btn btn-success btn-sm me-2">
                        <span v-if="isExporting">Exporting...</span>
                        <span v-else>Export Applications (CSV)</span>
                    </button>
                    <button @click="logout" class="btn btn-danger btn-sm">Logout</button>
                </div>
            </div>

            <div v-if="error" class="alert alert-danger shadow-sm">{{ error }}</div>
            <div v-if="success" class="alert alert-success shadow-sm" v-html="success"></div>

            <!-- Profile & Resume Upload Section -->
            <div class="card shadow mb-4">
                <div class="card-header bg-dark text-white">My Profile & Resume</div>
                <div class="card-body">
                    <form @submit.prevent="updateProfile" class="row g-3 align-items-center">
                        <div class="col-md-5">
                            <input type="text" class="form-control" v-model="studentSkills" placeholder="Enter Skills (e.g. Python, Vue, PostgreSQL)">
                        </div>
                        <div class="col-md-5">
                            <input type="file" class="form-control" @change="handleFileUpload" accept=".pdf,.doc,.docx">
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-primary w-100">Save Profile</button>
                        </div>
                    </form>
                </div>
            </div>

            <div class="row">
                <div class="col-md-5">
                    <div class="card shadow mb-4">
                        <div class="card-header bg-primary text-white">Available Placement Drives</div>
                        <div class="card-body p-0">
                            <table class="table table-hover mb-0">
                                <tbody>
                                    <tr v-for="drive in drives" :key="drive.id">
                                        <td class="p-3">
                                            <h5 class="mb-1 text-primary">{{ drive.job_title }}</h5>
                                            <strong>{{ drive.company_name }}</strong><br>
                                            <small class="text-muted">Branch: {{ drive.eligibility_branch }} | Min CGPA: {{ drive.eligibility_cgpa }}</small><br>
                                            <small class="text-danger">Deadline: {{ drive.deadline }}</small>
                                        </td>
                                        <td class="p-3 align-middle text-end">
                                            <button v-if="!drive.has_applied" @click="apply(drive.id)" class="btn btn-sm btn-outline-primary">Apply</button>
                                            <span v-else class="badge bg-secondary">Applied</span>
                                        </td>
                                    </tr>
                                    <tr v-if="drives.length === 0"><td colspan="2" class="text-center p-4">No active drives available.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="col-md-7">
                    <div class="card shadow">
                        <div class="card-header bg-secondary text-white">My Application Status & Interviews</div>
                        <div class="card-body">
                            <table class="table">
                                <thead><tr><th>Company & Role</th><th>Status</th><th>Interview & Feedback</th></tr></thead>
                                <tbody>
                                    <tr v-for="app in applications" :key="app.id">
                                        <td><strong>{{ app.company_name }}</strong><br>{{ app.job_title }}</td>
                                        <td class="align-middle">
                                            <span :class="{
                                                'badge bg-success': app.status === 'Selected', 
                                                'badge bg-danger': app.status === 'Rejected', 
                                                'badge bg-info text-dark': app.status === 'Shortlisted',
                                                'badge bg-warning text-dark': app.status === 'Applied'
                                            }">{{ app.status }}</span>
                                        </td>
                                        <td>
                                            <small v-if="app.interview_date" class="d-block text-primary"><strong>Date:</strong> {{ app.interview_date }}</small>
                                            <small v-if="app.feedback" class="d-block text-muted"><strong>Notes:</strong> {{ app.feedback }}</small>
                                            <small v-if="!app.interview_date && !app.feedback" class="text-muted">Awaiting response.</small>
                                        </td>
                                    </tr>
                                    <tr v-if="applications.length === 0"><td colspan="3" class="text-center">You haven't applied to any jobs yet.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            drives: [],
            applications: [],
            error: null,
            success: null,
            isExporting: false,
            studentSkills: '',
            studentName: '', // Added state for the name
            selectedFile: null
        }
    },
    async mounted() {
        if (!localStorage.getItem('token') || localStorage.getItem('role') !== 'student') return this.$router.push('/');
        
        // Ensure the profile fetches immediately on load
        await this.fetchProfile();
        await this.fetchDrives(); 
        await this.fetchApplications();
    },
    methods: {
        getHeaders() { 
            return { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + localStorage.getItem('token') }; 
        },
        async fetchProfile() {
            try {
                const res = await fetch('/api/student/me', { headers: this.getHeaders() });
                if (res.ok) {
                    const data = await res.json();
                    this.studentName = data.name;
                    if (data.skills) this.studentSkills = data.skills;
                }
            } catch (err) {
                console.error("Error fetching profile", err);
            }
        },
        async fetchDrives() {
            const res = await fetch('/api/student/drives', { headers: this.getHeaders() });
            if (res.ok) this.drives = await res.json();
        },
        async fetchApplications() {
            const res = await fetch('/api/student/applications', { headers: this.getHeaders() });
            if (res.ok) this.applications = await res.json();
        },
        async apply(driveId) {
            this.error = null; this.success = null;
            const res = await fetch('/api/student/apply/' + driveId, { method: 'POST', headers: this.getHeaders() });
            const data = await res.json();
            if (res.ok) { 
                this.success = data.message; 
                await this.fetchDrives(); 
                await this.fetchApplications(); 
            } else {
                this.error = data.message;
            }
        },
        async exportCSV() {
            this.error = null; this.success = null; this.isExporting = true;
            try {
                const res = await fetch('/api/student/export', { method: 'POST', headers: this.getHeaders() });
                const data = await res.json();
                if (res.ok) {
                    this.success = `${data.message} <br> <a href="${data.download_url}" target="_blank" class="btn btn-sm btn-link mt-2">Download File Here</a>`;
                } else {
                    this.error = data.message || "Failed to trigger export.";
                }
            } catch (err) {
                this.error = "Server error while exporting.";
            } finally {
                this.isExporting = false;
            }
        },
        handleFileUpload(event) {
            this.selectedFile = event.target.files[0];
        },
        async updateProfile() {
            this.error = null; this.success = null;
            const token = localStorage.getItem('token');
            const formData = new FormData();
            
            formData.append('skills', this.studentSkills);
            if (this.selectedFile) {
                formData.append('resume', this.selectedFile); 
            }

            try {
                const response = await fetch('/api/student/profile', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + token }, 
                    body: formData 
                });

                const data = await response.json();
                if (response.ok) {
                    this.success = "Profile updated successfully!";
                } else {
                    this.error = "Error: " + data.message;
                }
            } catch (error) {
                this.error = "Upload failed. Check server logs.";
            }
        },
        logout() { 
            localStorage.clear(); 
            this.$router.push('/'); 
        }
    }
};
// 2. Define the Login Component
const Login = {
    template: `
        <div class="row justify-content-center mt-5">
            <div class="col-md-4">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="card-title text-center mb-4">Placement Portal Login</h3>
                        <div v-if="error" class="alert alert-danger">{{ error }}</div>
                        <form @submit.prevent="loginUser">
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" v-model="email" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" v-model="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        <div class="mt-3 text-center">
                            <p>Don't have an account?</p>
                            <router-link to="/register/student" class="btn btn-sm btn-outline-secondary me-2">Register Student</router-link>
                            <router-link to="/register/company" class="btn btn-sm btn-outline-secondary">Register Company</router-link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() { return { email: '', password: '', error: null } },
    methods: {
        async loginUser() {
            this.error = null; 
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: this.email, password: this.password })
                });
                const data = await response.json();
                if (response.ok) {
                    localStorage.setItem('token', data.access_token);
                    localStorage.setItem('role', data.role);
                    if (data.role === 'admin') this.$router.push('/admin');
                    else if (data.role === 'company') this.$router.push('/company');
                    else if (data.role === 'student') this.$router.push('/student');
                } else {
                    this.error = data.message;
                }
            } catch (err) {
                this.error = 'Cannot connect to the server.';
            }
        }
    }
};

// 3. Define Student Registration Component
const StudentRegister = {
    template: `
        <div class="row justify-content-center mt-5 mb-5">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="card-title text-center mb-4">Student Registration</h3>
                        <div v-if="message" class="alert alert-info">{{ message }}</div>
                        <form @submit.prevent="registerStudent">
                            <div class="mb-3"><label>Name</label><input type="text" v-model="form.name" class="form-control" required></div>
                            <div class="mb-3"><label>Roll Number</label><input type="text" v-model="form.roll_number" class="form-control" required></div>
                            <div class="mb-3"><label>Email</label><input type="email" v-model="form.email" class="form-control" required></div>
                            <div class="mb-3"><label>Password</label><input type="password" v-model="form.password" class="form-control" required></div>
                            <div class="mb-3"><label>Branch</label><input type="text" v-model="form.branch" class="form-control" required></div>
                            <div class="mb-3"><label>CGPA</label><input type="number" step="0.01" v-model="form.cgpa" class="form-control" required></div>
                            <div class="mb-3"><label>Skills</label><textarea v-model="form.skills" class="form-control"></textarea></div>
                            <button type="submit" class="btn btn-success w-100">Register</button>
                        </form>
                        <div class="mt-3 text-center"><router-link to="/">Back to Login</router-link></div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() { return { form: { name: '', roll_number: '', email: '', password: '', branch: '', cgpa: '', skills: '' }, message: null } },
    methods: {
        async registerStudent() {
            try {
                const response = await fetch('/api/register/student', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });
                const data = await response.json();
                this.message = data.message;
                if (response.ok) setTimeout(() => this.$router.push('/'), 2000); // Send to login after 2 seconds
            } catch (err) { this.message = 'Error connecting to server.'; }
        }
    }
};

// 4. Define Company Registration Component
const CompanyRegister = {
    template: `
        <div class="row justify-content-center mt-5 mb-5">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h3 class="card-title text-center mb-4">Company Registration</h3>
                        <div v-if="message" class="alert alert-info">{{ message }}</div>
                        <form @submit.prevent="registerCompany">
                            <div class="mb-3"><label>Company Name</label><input type="text" v-model="form.name" class="form-control" required></div>
                            <div class="mb-3"><label>HR Contact Name</label><input type="text" v-model="form.hr_contact" class="form-control" required></div>
                            <div class="mb-3"><label>Email</label><input type="email" v-model="form.email" class="form-control" required></div>
                            <div class="mb-3"><label>Password</label><input type="password" v-model="form.password" class="form-control" required></div>
                            <div class="mb-3"><label>Website (Optional)</label><input type="url" v-model="form.website" class="form-control"></div>
                            <button type="submit" class="btn btn-success w-100">Register</button>
                        </form>
                        <div class="mt-3 text-center"><router-link to="/">Back to Login</router-link></div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() { return { form: { name: '', hr_contact: '', email: '', password: '', website: '' }, message: null } },
    methods: {
        async registerCompany() {
            try {
                const response = await fetch('/api/register/company', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });
                const data = await response.json();
                this.message = data.message;
                if (response.ok) setTimeout(() => this.$router.push('/'), 2000); // Send to login after 2 seconds
            } catch (err) { this.message = 'Error connecting to server.'; }
        }
    }
};

// 5. Configure Vue Router
const routes = [
    { path: '/', component: Login },
    { path: '/admin', component: AdminDashboard },
    { path: '/company', component: CompanyDashboard },
    { path: '/student', component: StudentDashboard },
    { path: '/register/student', component: StudentRegister },
    { path: '/register/company', component: CompanyRegister }
];

const router = VueRouter.createRouter({ history: VueRouter.createWebHashHistory(), routes });
const app = Vue.createApp({});
app.use(router);
app.mount('#app');