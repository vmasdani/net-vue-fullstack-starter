using DotNetEnv;
using Microsoft.EntityFrameworkCore;
using MySqlConnector;

var builder = WebApplication.CreateBuilder(args);

// Load environment variables from .env file
Env.Load("./.env");

// Extract the DB details from the environment
string dbName = Env.GetString("DB_NAME");
string dbHost = Env.GetString("DB_HOST");
string dbUsername = Env.GetString("DB_USERNAME");
string dbPassword = Env.GetString("DB_PASSWORD");

// Build the connection string using the values from the .env file
string connectionString = $"Server={dbHost};Database={dbName};User={dbUsername};Password={dbPassword};";

Console.WriteLine(connectionString);

// Configure MySQL with automatic server version detection
builder.Services.AddDbContext<AppDbContext>(options =>
{
    var connection = new MySqlConnection(connectionString);
    options.UseMySql(connection, ServerVersion.AutoDetect(connection));
});

var app = builder.Build();

// Apply pending migrations automatically
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    dbContext.Database.Migrate(); // Applies migrations on startup
}

// A simple endpoint to test if the API is running
app.MapGet("/", () => "Hello World!");

app.MapGet("/items", (AppDbContext ctx) => ctx.Items);

// Endpoint to check the database connection
app.MapGet("/test-connection", async (AppDbContext dbContext) =>
{
    return Results.Ok(new { Status = "Connection successful" });
});

app.Run();

// Define your DbContext
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    // Define your DbSets (tables) here
    public DbSet<Item> Items { get; set; }

    // Override SaveChanges to update timestamps
    public override int SaveChanges()
    {
        UpdateTimestamps();
        return base.SaveChanges();
    }

    public override Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        UpdateTimestamps();
        return base.SaveChangesAsync(cancellationToken);
    }

    // Method to set the CreatedAt and UpdatedAt fields
    private void UpdateTimestamps()
    {
        var entries = ChangeTracker.Entries<BaseModel>();

        foreach (var entry in entries)
        {
            if (entry.State == EntityState.Added)
            {
                entry.Entity.CreatedAt = DateTime.UtcNow;
                entry.Entity.UpdatedAt = DateTime.UtcNow;
            }
            else if (entry.State == EntityState.Modified)
            {
                entry.Entity.UpdatedAt = DateTime.UtcNow;
            }
        }
    }
}

public class Item : BaseModel
{
    public int Id { get; set; }
    public string? Name { get; set; }
}
public class BaseModel
{
    public DateTime? CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}
